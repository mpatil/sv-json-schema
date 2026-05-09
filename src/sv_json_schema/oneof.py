"""`oneOf` schema extension.

Treats a top-level `definitions/<Name>` entry of shape

    {
        "oneOf": [{"$ref": "#/definitions/A"}, {"$ref": "#/definitions/B"}, ...],
        "discriminator": {"propertyName": "kind"}
    }

as an SV base class with one concrete subclass per branch. The discriminator
value for each branch is read from that branch's `discriminator-property`
default, so each branch must supply a `default` for the discriminator field.

statham strips the `oneOf`/`discriminator` keywords during parsing, so the
metadata is harvested from the resolved schema dict before parsing.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, NamedTuple, Optional, Tuple


_AUTOTITLE = "_x_autotitle"


class OneOfBranch(NamedTuple):
    name: str
    value: str  # discriminator value


class OneOfSpec(NamedTuple):
    discriminator: str
    branches: Tuple[OneOfBranch, ...]


# {base_class_name: OneOfSpec}
OneOfMap = Mapping[str, OneOfSpec]
# {(owner_class_title, property_name): base_class_name}
OneOfPropMap = Mapping[Tuple[str, str], str]


class OneOfError(ValueError):
    """Raised when a `oneOf` definition lacks information needed for codegen."""


def _branch_name(branch: Mapping[str, Any]) -> str:
    return branch.get(_AUTOTITLE) or branch.get("title") or ""


def _branch_discriminator_value(
    branch: Mapping[str, Any], discriminator: str
) -> str:
    """Pull the default of `discriminator` out of a branch schema."""
    props = branch.get("properties") or {}
    field = props.get(discriminator)
    if not isinstance(field, dict):
        raise OneOfError(
            f"branch {_branch_name(branch)!r} has no `{discriminator}` property"
        )
    if "default" not in field:
        raise OneOfError(
            f"branch {_branch_name(branch)!r} property {discriminator!r} has "
            "no `default` (needed as the discriminator value)"
        )
    return str(field["default"])


def _spec_from_definition(name: str, node: Mapping[str, Any]) -> Optional[OneOfSpec]:
    if "oneOf" not in node:
        return None
    branches_raw = node["oneOf"]
    discriminator_field = node.get("discriminator")
    if not isinstance(discriminator_field, dict) or "propertyName" not in discriminator_field:
        raise OneOfError(
            f"oneOf definition {name!r} requires a `discriminator: {{propertyName: ...}}`"
        )
    discriminator = discriminator_field["propertyName"]
    branches: List[OneOfBranch] = []
    for branch in branches_raw:
        if not isinstance(branch, dict):
            continue
        branches.append(
            OneOfBranch(
                name=_branch_name(branch),
                value=_branch_discriminator_value(branch, discriminator),
            )
        )
    if len(branches) < 2:
        raise OneOfError(
            f"oneOf definition {name!r} needs at least two branches (got {len(branches)})"
        )
    return OneOfSpec(discriminator=discriminator, branches=tuple(branches))


def collect_oneofs(schema: Mapping[str, Any]) -> Dict[str, OneOfSpec]:
    """Walk `definitions` and collect every oneOf base."""
    out: Dict[str, OneOfSpec] = {}
    for name, node in (schema.get("definitions") or {}).items():
        if name == _AUTOTITLE or not isinstance(node, dict):
            continue
        spec = _spec_from_definition(name, node)
        if spec is not None:
            out[name] = spec
    return out


def collect_oneof_props(schema: Mapping[str, Any]) -> Dict[Tuple[str, str], str]:
    """Walk every property and tag those whose schema is itself a oneOf base.

    Returns {(owner_title, prop_name): base_name}.
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
            if "oneOf" in target:
                base = target.get(_AUTOTITLE) or target.get("title")
                if base:
                    out[(title, prop_name)] = base
            visit(prop_schema, title)
        for name, child in (node.get("definitions") or {}).items():
            if name == _AUTOTITLE:
                continue
            visit(child, title)

    visit(schema, schema.get(_AUTOTITLE, schema.get("title", "")))
    return out
