"""statham → SystemVerilog serializer.

Translates a parsed statham schema element tree into the dict structure the
Mako templates render. Hex/binary string fields are surfaced via a side-table
of bit-vector metadata (see ``serializers.bitvec``); statham's universal model
stays untouched.
"""

from typing import Any, Dict, List, Optional, Tuple, TypeVar

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


T = TypeVar("T")


def _maybe(value: Any, default: T) -> T:
    """Collapse statham's ``Maybe[T]`` to ``T``, substituting `default` for ``NotPassed``."""
    return default if isinstance(value, NotPassed) else value


def _array_items(elem: Element) -> Element:
    return elem.items if isinstance(elem, Array) else elem


def sv_type(elem: Element, bitvec: Optional[BitVec]) -> Tuple[str, bool]:
    """Map an element to (SV type, isRand)."""
    if elem is None:
        return "???", False
    inner = _array_items(elem)
    if bitvec is not None:
        return "logic", True
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


def json_type(elem: Element, bitvec: Optional[BitVec]) -> Optional[str]:
    """Categorise a property for the Mako template's macro dispatch."""
    if elem is None:
        return None
    is_array = isinstance(elem, Array)
    inner = _array_items(elem)
    if bitvec is not None:
        cat = bitvec.radix  # "hex" | "binary"
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


def sv_def(elem: Element, bitvec: Optional[BitVec]) -> Optional[str]:
    """Render the SV literal for a default value (or None if absent)."""
    if elem is None or isinstance(elem, Array):
        return None if elem is None else sv_def(elem.items, bitvec)
    if isinstance(elem.default, NotPassed):
        return None
    raw = elem.default
    if bitvec is not None:
        if bitvec.radix == RADIX_HEX:
            return f"'h{str(raw)[2:]}"
        if bitvec.radix == RADIX_BINARY:
            return f"'b{str(raw)[2:]}"
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


def _array_constraints(p: str, elem: Array) -> Dict[str, Any]:
    return {
        "maxItems": _maybe(elem.maxItems, None),
        "minItems": _maybe(elem.minItems, None),
        "maximum": (
            f"foreach ( m_{p}[i] ) {{ m_{p}[i] <= {elem.items.maximum} }}; "
            if getattr(elem.items, "maximum", None) is not None
            and not isinstance(elem.items.maximum, NotPassed)
            else ""
        ),
        "minimum": (
            f"foreach ( m_{p}[i] ) {{ m_{p}[i] >= {elem.items.minimum} }}; "
            if getattr(elem.items, "minimum", None) is not None
            and not isinstance(elem.items.minimum, NotPassed)
            else ""
        ),
        "isEnum": not isinstance(elem.items.enum, NotPassed),
    }


def _scalar_constraints(p: str, elem: Element) -> Dict[str, Any]:
    return {
        "maximum": (
            f"m_{p} <= {elem.maximum}; "
            if getattr(elem, "maximum", None) is not None
            and not isinstance(elem.maximum, NotPassed)
            else ""
        ),
        "minimum": (
            f"m_{p} >= {elem.minimum}; "
            if getattr(elem, "minimum", None) is not None
            and not isinstance(elem.minimum, NotPassed)
            else ""
        ),
        "isEnum": not isinstance(elem.enum, NotPassed),
    }


def _serialize_classes(
    elements: Tuple[Element, ...], widths: WidthMap
) -> Dict[str, List[Dict[str, Any]]]:
    cs: Dict[str, List[Dict[str, Any]]] = {}
    for o in orderer(*elements):
        if not isinstance(o.enum, NotPassed):
            continue
        owner = str(o)
        ms: List[Dict[str, Any]] = []
        for p in o.properties:
            elem = o._properties[p].element
            bv = widths.get((owner, p))
            ty, is_rand = sv_type(elem, bv)
            prop: Dict[str, Any] = {
                "name": p,
                "type_cat": json_type(elem, bv),
                "type": ty,
                "isRand": is_rand,
                "def": sv_def(elem, bv),
                "width": sv_width(bv),
                "isArray": isinstance(elem, Array),
                "isRequired": bool(o._properties[p].required),
            }
            prop.update(
                _array_constraints(p, elem)
                if isinstance(elem, Array)
                else _scalar_constraints(p, elem)
            )
            ms.append(prop)
        cs[owner] = ms
    return cs


def serialize_sv(
    elements: Tuple[Element, ...], widths: Optional[WidthMap] = None
) -> Dict[str, Any]:
    widths = widths or {}
    return {
        "enums": _serialize_enums(elements),
        "classes": _serialize_classes(elements, widths),
    }
