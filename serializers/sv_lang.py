"""statham → SystemVerilog serializer.

Translates a parsed statham schema element tree into the dict structure the
Mako templates render. Hex/binary string fields are surfaced via a side-table
of bit-vector metadata (see ``serializers.bitvec``); statham's universal model
stays untouched.
"""

import re
from typing import Any, Dict, List, NamedTuple, Optional, Tuple, TypeVar

from statham.schema.constants import NotPassed
from statham.schema.elements import (
    Array,
    Boolean,
    Element,
    Integer,
    Number,
    String,
)
from statham.schema.elements.meta import ObjectMeta
from statham.serializers.orderer import orderer

from serializers.bitvec import BitVec, RADIX_BINARY, RADIX_HEX, WidthMap
from serializers.oneof import OneOfMap, OneOfPropMap


T = TypeVar("T")


_SV_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class PlainEnumError(ValueError):
    """Raised when a plain string enum can't be projected onto SV identifiers."""


class PlainEnum(NamedTuple):
    kind: str  # "str" or "int"
    values: Tuple[Any, ...]
    typedef: Optional[str]  # set for "str" kind only


def _plain_enum_for(owner: str, prop: str, elem: Element) -> Optional[PlainEnum]:
    inner = _array_items(elem)
    if isinstance(inner.enum, NotPassed):
        return None
    if isinstance(inner, String):
        values = tuple(inner.enum)
        for v in values:
            if not _SV_IDENT_RE.fullmatch(v):
                raise PlainEnumError(
                    f"{owner}.{prop}: enum value {v!r} is not a valid SV identifier; "
                    "string-enum values must round-trip via uvm_enum_wrapper "
                    "(letters, digits, underscores; not starting with a digit)."
                )
        return PlainEnum("str", values, f"{owner}_{prop}_e")
    if isinstance(inner, Integer):
        return PlainEnum("int", tuple(inner.enum), None)
    return None


def _maybe(value: Any, default: T) -> T:
    """Collapse statham's ``Maybe[T]`` to ``T``, substituting `default` for ``NotPassed``."""
    return default if isinstance(value, NotPassed) else value


def _array_items(elem: Element) -> Element:
    return elem.items if isinstance(elem, Array) else elem


def sv_type(
    elem: Element, bitvec: Optional[BitVec], plain_enum: Optional[PlainEnum] = None
) -> Tuple[str, bool]:
    """Map an element to (SV type, isRand)."""
    if elem is None:
        return "???", False
    inner = _array_items(elem)
    if bitvec is not None:
        return "logic", True
    if plain_enum is not None and plain_enum.kind == "str":
        return plain_enum.typedef, True
    if isinstance(inner, Integer):
        return "int", True
    if isinstance(inner, Number):
        return "real", False
    if isinstance(inner, Boolean):
        return "bit", True
    if isinstance(inner, String):
        return "string", False
    if isinstance(inner, ObjectMeta):
        return f"{inner}", True
    return "???", False


def sv_width(bitvec: Optional[BitVec]) -> Optional[int]:
    return None if bitvec is None else bitvec.width


def json_type(
    elem: Element, bitvec: Optional[BitVec], plain_enum: Optional[PlainEnum] = None
) -> Optional[str]:
    """Categorise a property for the Mako template's macro dispatch."""
    if elem is None:
        return None
    is_array = isinstance(elem, Array)
    inner = _array_items(elem)
    if bitvec is not None:
        cat = bitvec.radix  # "hex" | "binary"
    elif plain_enum is not None and plain_enum.kind == "str":
        cat = "enum"  # reuse the existing typedef-enum macro path
    elif plain_enum is not None and plain_enum.kind == "int":
        cat = "enum_int"
    elif isinstance(inner, Integer) or isinstance(inner, Number):
        cat = "int"
    elif isinstance(inner, Boolean):
        cat = "bool"
    elif isinstance(inner, String):
        cat = "string"
    elif isinstance(inner, ObjectMeta):
        cat = "object" if isinstance(inner.enum, NotPassed) else "enum"
    else:
        return None
    return f"{cat}_array" if is_array else cat


def sv_def(
    elem: Element, bitvec: Optional[BitVec], plain_enum: Optional[PlainEnum] = None
) -> Optional[str]:
    """Render the SV literal for a default value (or None if absent)."""
    if elem is None or isinstance(elem, Array):
        return None if elem is None else sv_def(elem.items, bitvec, plain_enum)
    if isinstance(elem.default, NotPassed):
        return None
    raw = elem.default
    if bitvec is not None:
        if bitvec.radix == RADIX_HEX:
            return f"'h{str(raw)[2:]}"
        if bitvec.radix == RADIX_BINARY:
            return f"'b{str(raw)[2:]}"
    if plain_enum is not None and plain_enum.kind == "str":
        # Default emitted as the bare enum identifier (matches the typedef).
        return f"{raw}"
    if isinstance(elem, (Integer, Number)):
        return f"{raw}"
    if isinstance(elem, Boolean):
        return f"{1 if raw else 0}"
    if isinstance(elem, String):
        return f"\"{raw}\""
    if isinstance(elem, ObjectMeta):
        return f"{raw}"
    return None


def _serialize_enums(elements: Tuple[Element, ...]) -> Dict[str, List[str]]:
    es: Dict[str, List[str]] = {}
    for o in orderer(*elements):
        if isinstance(o.enum, NotPassed):
            continue
        es[str(o)] = [k if v is None else f"{k}={v}" for k, v in o.enum.items()]
    return es


_RANGE_KEYWORDS: Tuple[Tuple[str, str], ...] = (
    ("minimum", ">="),
    ("maximum", "<="),
    ("exclusiveMinimum", ">"),
    ("exclusiveMaximum", "<"),
)


def _attr(elem: Element, name: str) -> Any:
    """Return statham element attr or None when absent / NotPassed."""
    val = getattr(elem, name, None)
    if val is None or isinstance(val, NotPassed):
        return None
    return val


def _range_constraints(target: str, elem: Element) -> List[str]:
    """Build the list of SV range expressions (no trailing semicolons)."""
    out: List[str] = []
    for attr, op in _RANGE_KEYWORDS:
        bound = _attr(elem, attr)
        if bound is not None:
            out.append(f"{target} {op} {bound}")
    multiple_of = _attr(elem, "multipleOf")
    if multiple_of is not None:
        out.append(f"{target} % {multiple_of} == 0")
    return out


def _array_constraints(p: str, elem: Array) -> Dict[str, Any]:
    item_parts = _range_constraints(f"m_{p}[i]", elem.items)
    range_constraints: List[str] = []
    if item_parts:
        range_constraints.append(
            f"foreach (m_{p}[i]) {{ {'; '.join(item_parts)}; }}"
        )
    return {
        "maxItems": _maybe(elem.maxItems, None),
        "minItems": _maybe(elem.minItems, None),
        "rangeConstraints": range_constraints,
        "uniqueItems": bool(getattr(elem, "uniqueItems", False)),
        "isEnum": not isinstance(elem.items.enum, NotPassed),
    }


def _scalar_constraints(p: str, elem: Element) -> Dict[str, Any]:
    return {
        "rangeConstraints": _range_constraints(f"m_{p}", elem),
        "uniqueItems": False,
        "isEnum": not isinstance(elem.enum, NotPassed),
    }


def _branch_to_base(oneofs: OneOfMap) -> Dict[str, str]:
    """Reverse-index oneOf branches: branch_class_name -> base_class_name."""
    return {b.name: base for base, spec in oneofs.items() for b in spec.branches}


def _serialize_classes(
    elements: Tuple[Element, ...],
    widths: WidthMap,
    oneofs: OneOfMap,
    oneof_props: OneOfPropMap,
    string_enums: Dict[str, List[str]],
) -> Dict[str, Dict[str, Any]]:
    branch_to_base = _branch_to_base(oneofs)
    cs: Dict[str, Dict[str, Any]] = {}
    for o in orderer(*elements):
        if not isinstance(o.enum, NotPassed):
            continue
        owner = str(o)
        ms: List[Dict[str, Any]] = []
        for p in o.properties:
            elem = o._properties[p].element
            bv = widths.get((owner, p))
            pe = _plain_enum_for(owner, p, elem)
            ty, is_rand = sv_type(elem, bv, pe)
            base = oneof_props.get((owner, p))
            if base is not None:
                # Override inferred type/category with the oneOf base class.
                ty = base
                is_rand = False  # oneOf-typed fields aren't safe to randomize
                cat = "oneof_array" if isinstance(elem, Array) else "oneof"
            else:
                cat = json_type(elem, bv, pe)
            if pe is not None and pe.kind == "str":
                string_enums[pe.typedef] = list(pe.values)
            prop: Dict[str, Any] = {
                "name": p,
                "type_cat": cat,
                "type": ty,
                "isRand": is_rand,
                "def": sv_def(elem, bv, pe),
                "width": sv_width(bv),
                "isArray": isinstance(elem, Array),
                "isRequired": bool(o._properties[p].required),
                "oneOfBase": base,
                "enumIntValues": (
                    list(pe.values) if pe is not None and pe.kind == "int" else None
                ),
            }
            prop.update(
                _array_constraints(p, elem)
                if isinstance(elem, Array)
                else _scalar_constraints(p, elem)
            )
            ms.append(prop)
        cs[owner] = {
            "members": ms,
            "extends": branch_to_base.get(owner, "uvm_object"),
            "strict": getattr(o, "additionalProperties", True) is False,
        }
    return cs


def _serialize_oneofs(oneofs: OneOfMap) -> Dict[str, Dict[str, Any]]:
    """Render oneOf base classes for the Mako template."""
    return {
        base: {
            "discriminator": spec.discriminator,
            "branches": [
                {"name": b.name, "value": b.value} for b in spec.branches
            ],
        }
        for base, spec in oneofs.items()
    }


def serialize_sv(
    elements: Tuple[Element, ...],
    widths: Optional[WidthMap] = None,
    oneofs: Optional[OneOfMap] = None,
    oneof_props: Optional[OneOfPropMap] = None,
) -> Dict[str, Any]:
    widths = widths or {}
    oneofs = oneofs or {}
    oneof_props = oneof_props or {}
    string_enums: Dict[str, List[str]] = {}
    classes = _serialize_classes(elements, widths, oneofs, oneof_props, string_enums)
    enums = _serialize_enums(elements)
    enums.update(string_enums)
    return {
        "enums": enums,
        "classes": classes,
        "oneOfs": _serialize_oneofs(oneofs),
    }
