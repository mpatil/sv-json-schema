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

from sv_json_schema.bitvec import BitVec, RADIX_BINARY, RADIX_HEX, WidthMap
from sv_json_schema.intformat import IntFormatMap
from sv_json_schema.oneof import OneOfMap, OneOfPropMap
from sv_json_schema.recursive import RecursiveRefMap, is_stub_class_name


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


def _integer_sv_type(int_format: Optional[str]) -> str:
    """Choose between SV `int` and `longint` based on the harvested `format`."""
    return "longint" if int_format == "int64" else "int"


def integer_bits(int_format: Optional[str]) -> int:
    """Bit width for printer dispatch on integer-typed properties."""
    return 64 if _integer_sv_type(int_format) == "longint" else 32


def sv_type(
    elem: Element,
    bitvec: Optional[BitVec],
    plain_enum: Optional[PlainEnum] = None,
    int_format: Optional[str] = None,
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
        return _integer_sv_type(int_format), True
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
    raw = _attr(elem, "default")
    if raw is None:
        # Promote `const` to default when no explicit default is given.
        raw = _attr(elem, "const")
        if raw is None:
            return None
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


def _sv_string_literal(s: Any) -> str:
    """Encode a Python string into an SV double-quoted literal."""
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _validation_checks(p: str, elem: Element) -> List[str]:
    """Build SV uvm_error snippets for declarative scalar checks.

    Covers `const`, `minLength`, `maxLength`. Bound to scalar properties only;
    array variants would need a foreach wrapper that we don't generate yet.
    """
    if isinstance(elem, Array):
        return []
    checks: List[str] = []

    const_val = _attr(elem, "const")
    if const_val is not None:
        if isinstance(elem, String):
            literal = _sv_string_literal(const_val)
            checks.append(
                f"if (m_{p} != {literal}) "
                f"`uvm_error(get_full_name(), $sformatf("
                f"\"'{p}' must equal const %s, got '%s'\", {literal}, m_{p}))"
            )
        elif isinstance(elem, Boolean):
            v = "1" if const_val else "0"
            checks.append(
                f"if (m_{p} != {v}) "
                f"`uvm_error(get_full_name(), $sformatf("
                f"\"'{p}' must equal const {v}, got %0d\", m_{p}))"
            )
        elif isinstance(elem, (Integer, Number)):
            checks.append(
                f"if (m_{p} != {const_val}) "
                f"`uvm_error(get_full_name(), $sformatf("
                f"\"'{p}' must equal const {const_val}, got %0d\", m_{p}))"
            )

    if isinstance(elem, String):
        min_len = _attr(elem, "minLength")
        if min_len is not None:
            checks.append(
                f"if (m_{p}.len() < {min_len}) "
                f"`uvm_error(get_full_name(), $sformatf("
                f"\"'{p}' length %0d below minLength {min_len}\", m_{p}.len()))"
            )
        max_len = _attr(elem, "maxLength")
        if max_len is not None:
            checks.append(
                f"if (m_{p}.len() > {max_len}) "
                f"`uvm_error(get_full_name(), $sformatf("
                f"\"'{p}' length %0d above maxLength {max_len}\", m_{p}.len()))"
            )

    return checks


def _branch_to_base(oneofs: OneOfMap) -> Dict[str, str]:
    """Reverse-index oneOf branches: branch_class_name -> base_class_name."""
    return {b.name: base for base, spec in oneofs.items() for b in spec.branches}


def _serialize_classes(
    elements: Tuple[Element, ...],
    widths: WidthMap,
    oneofs: OneOfMap,
    oneof_props: OneOfPropMap,
    string_enums: Dict[str, List[str]],
    int_formats: IntFormatMap,
    recursive_refs: RecursiveRefMap,
) -> Dict[str, Dict[str, Any]]:
    branch_to_base = _branch_to_base(oneofs)
    cs: Dict[str, Dict[str, Any]] = {}
    for o in orderer(*elements):
        if not isinstance(o.enum, NotPassed):
            continue
        owner = str(o)
        if is_stub_class_name(owner):
            # Synthetic class introduced by `serializers.recursive` to break a
            # statham parse cycle. Its only job was to give statham a typed
            # placeholder; the real type is the recursive target, which is
            # already in `recursive_refs`.
            continue
        ms: List[Dict[str, Any]] = []
        for p in o.properties:
            elem = o._properties[p].element
            bv = widths.get((owner, p))
            pe = _plain_enum_for(owner, p, elem)
            int_fmt = int_formats.get((owner, p))
            ty, is_rand = sv_type(elem, bv, pe, int_fmt)
            base = oneof_props.get((owner, p))
            recursive_target = recursive_refs.get((owner, p))
            if base is not None:
                # Override inferred type/category with the oneOf base class.
                ty = base
                is_rand = False  # oneOf-typed fields aren't safe to randomize
                cat = "oneof_array" if isinstance(elem, Array) else "oneof"
            elif recursive_target is not None:
                # Self-referential field — don't randomize (would infinite-loop)
                # and don't auto-instantiate in post_randomize.
                ty = recursive_target
                is_rand = False
                cat = "object_array" if isinstance(elem, Array) else "object"
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
                "validationChecks": _validation_checks(p, elem),
                "bits": integer_bits(int_fmt),
                "description": _attr(elem, "description"),
                "isRecursiveRef": recursive_target is not None,
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
            "description": _attr(o, "description"),
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
    int_formats: Optional[IntFormatMap] = None,
    recursive_refs: Optional[RecursiveRefMap] = None,
) -> Dict[str, Any]:
    widths = widths or {}
    oneofs = oneofs or {}
    oneof_props = oneof_props or {}
    int_formats = int_formats or {}
    recursive_refs = recursive_refs or {}
    string_enums: Dict[str, List[str]] = {}
    classes = _serialize_classes(
        elements, widths, oneofs, oneof_props, string_enums, int_formats,
        recursive_refs,
    )
    enums = _serialize_enums(elements)
    enums.update(string_enums)
    return {
        "enums": enums,
        "classes": classes,
        "oneOfs": _serialize_oneofs(oneofs),
    }
