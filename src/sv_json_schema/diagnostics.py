"""Diagnostics for JSON Schema keywords that the SV generator silently drops.

Goal: when a schema validates fine via a third-party JSON Schema validator
but the generator can't model one of its keywords, surface that loudly so
the user knows the SV layer won't enforce the constraint at simulation
time. Walk the resolved schema dict and emit one Diagnostic per dropped
keyword, with the JSON-Pointer-style path for context.

Usage:

    diags = collect_diagnostics(raw_schema_dict)
    for d in diags:
        print(d.format(), file=sys.stderr)
    if strict and diags:
        sys.exit(1)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Mapping


# Standard assertion keywords that we don't emit anything for. A schema that
# uses these will validate via third-party tools but the generated SV will
# carry no equivalent runtime check.
_UNSUPPORTED_ASSERTIONS = frozenset({
    # Composition
    "allOf",
    "anyOf",
    "not",
    # Conditional
    "if",
    "then",
    "else",
    # String / object patterns
    "pattern",
    "patternProperties",
    # Dependencies
    "dependencies",
    "dependentRequired",
    "dependentSchemas",
    # Array
    "contains",
    "minContains",
    "maxContains",
    "additionalItems",
    # Object
    "minProperties",
    "maxProperties",
    "propertyNames",
    "unevaluatedItems",
    "unevaluatedProperties",
})

# `format` values that map to specific SV constructs. Anything else is dropped.
_SUPPORTED_STRING_FORMATS = frozenset({"hex", "binary"})
_SUPPORTED_INTEGER_FORMATS = frozenset({"int32", "int64"})

# Keys we consume internally and shouldn't recurse into for unsupported-keyword
# detection (they're part of a property's own metadata, not nested schemas).
_NON_SCHEMA_KEYS = frozenset({
    "_x_autotitle",
    "title",
    "description",
    "$schema",
    "$id",
    "$comment",
    "examples",
    "readOnly",
    "writeOnly",
    "deprecated",
    "version",
    "default",
    "const",
    "enum",
    "format",
    "type",
    "minimum",
    "maximum",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "multipleOf",
    "minItems",
    "maxItems",
    "uniqueItems",
    "minLength",
    "maxLength",
    "required",
    "x-sv-width",
    "discriminator",
})


@dataclass(frozen=True)
class Diagnostic:
    path: str
    keyword: str
    message: str

    def format(self) -> str:
        return f"{self.path or '<root>'}: {self.message}"


def collect_diagnostics(schema: Mapping[str, Any]) -> List[Diagnostic]:
    out: List[Diagnostic] = []
    _walk(schema, "", out)
    return out


def _walk(node: Any, path: str, out: List[Diagnostic]) -> None:
    if not isinstance(node, dict):
        return

    for key in node:
        if key in _UNSUPPORTED_ASSERTIONS:
            out.append(
                Diagnostic(
                    path=path,
                    keyword=key,
                    message=(
                        f"keyword `{key}` is not honored by the SV generator. "
                        "The schema will validate via JSON-Schema tools but the "
                        "generated SV will not enforce the corresponding constraint."
                    ),
                )
            )

    # `additionalProperties: <schema>` (we only support the bool form)
    ap = node.get("additionalProperties")
    if isinstance(ap, dict):
        out.append(
            Diagnostic(
                path=path,
                keyword="additionalProperties",
                message=(
                    "`additionalProperties: <schema>` (validating extra keys "
                    "against a schema) is not supported. Only "
                    "`additionalProperties: false` is honored."
                ),
            )
        )

    # `type` as an array: multi-type union.
    typ = node.get("type")
    if isinstance(typ, list):
        out.append(
            Diagnostic(
                path=path,
                keyword="type",
                message=(
                    f"multi-type union `{typ}` is not supported. The SV side "
                    "will use only the first applicable type, if any."
                ),
            )
        )
    elif typ == "null":
        out.append(
            Diagnostic(
                path=path,
                keyword="type",
                message="`type: null` is not supported.",
            )
        )

    # `format` strings the generator doesn't surface in SV.
    fmt = node.get("format")
    if isinstance(fmt, str):
        if typ == "string" and fmt not in _SUPPORTED_STRING_FORMATS:
            out.append(
                Diagnostic(
                    path=path,
                    keyword="format",
                    message=(
                        f"`format: \"{fmt}\"` on a string field is recognised "
                        "by JSON-Schema validators but is not surfaced in the "
                        "generated SV. Only `hex` and `binary` produce specific "
                        "SV types."
                    ),
                )
            )
        elif typ == "integer" and fmt not in _SUPPORTED_INTEGER_FORMATS:
            out.append(
                Diagnostic(
                    path=path,
                    keyword="format",
                    message=(
                        f"`format: \"{fmt}\"` on an integer field is not "
                        "honored. Only `int32` and `int64` map to SV types."
                    ),
                )
            )

    # Recurse into structural children. We only descend into places that hold
    # nested schemas: `properties.*`, `items` (single-schema or each tuple
    # entry), `definitions`/`$defs`, and the composition keywords (recurse
    # so we still surface diagnostics inside them, even though we already
    # flagged the keyword itself).
    for prop_name, prop_schema in (node.get("properties") or {}).items():
        if prop_name == "_x_autotitle":
            continue
        _walk(prop_schema, _join(path, "properties", prop_name), out)

    items = node.get("items")
    if isinstance(items, dict):
        _walk(items, _join(path, "items"), out)
    elif isinstance(items, list):
        for i, item in enumerate(items):
            _walk(item, _join(path, "items", str(i)), out)

    for defs_key in ("definitions", "$defs"):
        for name, child in (node.get(defs_key) or {}).items():
            if name == "_x_autotitle":
                continue
            _walk(child, _join(path, defs_key, name), out)

    for comp in ("allOf", "anyOf", "oneOf"):
        for i, child in enumerate(node.get(comp) or ()):
            _walk(child, _join(path, comp, str(i)), out)

    for kw in ("not", "if", "then", "else"):
        child = node.get(kw)
        if isinstance(child, dict):
            _walk(child, _join(path, kw), out)


def _join(*parts: str) -> str:
    return "/".join(p for p in parts if p)
