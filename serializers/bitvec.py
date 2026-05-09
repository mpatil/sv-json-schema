"""Bit-vector schema extension.

Treats `{"type": "string", "format": "hex" | "binary", "x-sv-width": N}` as a
SystemVerilog bit-vector field (radix + width in bits) rather than a free-form
JSON string. statham-schema's `format_checker` is extended in-place so the
schema still validates without forking the upstream library, and `x-sv-width`
is harvested directly from the resolved schema dict — statham strips unknown
kwargs before constructing Element instances, so the width has to be captured
before that happens.
"""

from typing import Any, Dict, Iterable, Mapping, NamedTuple, Optional, Tuple

from statham.schema.validation.format import format_checker

RADIX_HEX = "hex"
RADIX_BINARY = "binary"
DEFAULT_HEX_WIDTH = 32
DEFAULT_BINARY_WIDTH = 32

WIDTH_KEYWORD = "x-sv-width"


class BitVec(NamedTuple):
    radix: str
    width: int


# (class_title, property_name) -> BitVec
WidthMap = Mapping[Tuple[str, str], BitVec]


def register_format_validators() -> None:
    """Teach statham's format_checker how to validate hex and binary strings.

    Idempotent: re-registering replaces the previous callable.
    """

    @format_checker.register(RADIX_HEX)
    def _is_hex(value: str) -> bool:
        if not isinstance(value, str):
            return False
        body = value[2:] if value[:2] in ("0x", "0X") else value
        try:
            int(body, 16)
        except ValueError:
            return False
        return bool(body)

    @format_checker.register(RADIX_BINARY)
    def _is_binary(value: str) -> bool:
        if not isinstance(value, str):
            return False
        body = value[2:] if value[:2] in ("0b", "0B") else value
        return bool(body) and all(c in "01" for c in body)


def _bitvec_from_schema(node: Mapping[str, Any]) -> Optional[BitVec]:
    """If `node` describes a hex/binary string, return its BitVec metadata."""
    if node.get("type") != "string":
        return None
    fmt = node.get("format")
    if fmt == RADIX_HEX:
        return BitVec(RADIX_HEX, int(node.get(WIDTH_KEYWORD, DEFAULT_HEX_WIDTH)))
    if fmt == RADIX_BINARY:
        return BitVec(RADIX_BINARY, int(node.get(WIDTH_KEYWORD, DEFAULT_BINARY_WIDTH)))
    return None


_AUTOTITLE = "_x_autotitle"


def _node_title(node: Mapping[str, Any], fallback: str) -> str:
    """statham's title_labeller injects the class name as `_x_autotitle`."""
    return node.get(_AUTOTITLE, node.get("title", fallback))


def collect_bitvec_widths(schema: Mapping[str, Any]) -> Dict[Tuple[str, str], BitVec]:
    """Walk a resolved JSON Schema dict and collect bit-vector metadata.

    Keys are (containing-object-title, property-name); values are BitVec.
    Array items inherit their containing property's key (the SV serializer
    treats arrays uniformly with their item type).
    """
    widths: Dict[Tuple[str, str], BitVec] = {}

    def visit_props(node: Mapping[str, Any], owner_title: str) -> None:
        for prop_name, prop_schema in (node.get("properties") or {}).items():
            if prop_name == _AUTOTITLE or not isinstance(prop_schema, dict):
                continue
            target = prop_schema
            if prop_schema.get("type") == "array":
                items = prop_schema.get("items")
                if isinstance(items, dict):
                    target = items
            bv = _bitvec_from_schema(target)
            if bv is not None:
                widths[(owner_title, prop_name)] = bv
            visit(prop_schema, owner_title)

    def visit(node: Any, parent_title: str) -> None:
        if not isinstance(node, dict):
            return
        title = _node_title(node, parent_title)
        visit_props(node, title)
        for items in (node.get("items"),):
            visit(items, title)
        for name, child in (node.get("definitions") or {}).items():
            if name == _AUTOTITLE:
                continue
            visit(child, title)
        for keyword in ("oneOf", "anyOf", "allOf"):
            for child in node.get(keyword) or ():
                visit(child, title)

    visit(schema, _node_title(schema, ""))
    return widths


def is_bitvec(widths: WidthMap, owner: str, prop: str) -> bool:
    return (owner, prop) in widths


def get(widths: WidthMap, owner: str, prop: str) -> Optional[BitVec]:
    return widths.get((owner, prop))
