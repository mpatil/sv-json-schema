"""Integer `format` keyword harvester.

statham's NumericElement (Integer / Number) constructor doesn't accept
`format`, so `_keyword_filter` strips it during parsing. The format is
nevertheless useful for SV codegen: `int32` maps to `int`, `int64` to
`longint`. Walks the resolved schema dict before parsing and records the
format for each integer property.

Same pattern as `bitvec.collect_bitvec_widths` / `oneof.collect_oneof_props`.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Tuple


_AUTOTITLE = "_x_autotitle"

# {(owner_class_title, property_name): format_str}
IntFormatMap = Mapping[Tuple[str, str], str]


def collect_int_formats(schema: Mapping[str, Any]) -> Dict[Tuple[str, str], str]:
    """Walk every property and record `format` on integer-typed schemas.

    Returns the integer format keyed by (owner_title, prop_name).
    Array items inherit their containing property's key.
    """
    out: Dict[Tuple[str, str], str] = {}

    def visit(node: Any, parent_title: str) -> None:
        if not isinstance(node, dict):
            return
        title = node.get(_AUTOTITLE, node.get("title", parent_title))
        for prop_name, prop_schema in (node.get("properties") or {}).items():
            if prop_name == _AUTOTITLE or not isinstance(prop_schema, dict):
                continue
            target = prop_schema
            if prop_schema.get("type") == "array":
                items = prop_schema.get("items")
                if isinstance(items, dict):
                    target = items
            if target.get("type") == "integer" and isinstance(
                target.get("format"), str
            ):
                out[(title, prop_name)] = target["format"]
            visit(prop_schema, title)
        for name, child in (node.get("definitions") or {}).items():
            if name == _AUTOTITLE:
                continue
            visit(child, title)

    visit(schema, schema.get(_AUTOTITLE, schema.get("title", "")))
    return out
