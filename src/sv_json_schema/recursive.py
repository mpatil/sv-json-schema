"""Recursive `$ref` support: break cycles before statham parses.

statham raises FeatureNotImplementedError on cyclic dependencies, so we
preprocess the materialized schema dict to replace each in-cycle alias with
a stub `{"type": "object", "x-sv-recursive-ref": <name>}`. statham then
sees a regular object element at that spot; the SV serializer reads the
`x-sv-recursive-ref` side-table to override the property's type back to
the target class.

Scope (v1): direct self-recursion through any depth of `properties` /
`items` nesting. A definition that aliases another definition (mutual
recursion `A → B → A`) is left as a remaining cyclic schema and statham
will raise as before.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Set, Tuple


_AUTOTITLE = "_x_autotitle"
_RECURSIVE_KEY = "x-sv-recursive-ref"


# {(owner_class_title, property_name): target_class_name}
RecursiveRefMap = Mapping[Tuple[str, str], str]


# Suffix is chosen to survive statham's title sanitiser (which strips
# underscores and camel-cases segments) so we can recognise stub classes
# after parsing by their final class name.
_STUB_SUFFIX = "RecStub"


def stub_title_for(target_name: str) -> str:
    return f"{target_name}{_STUB_SUFFIX}"


def _stub(target_name: str) -> Dict[str, Any]:
    # statham requires a title on every object schema. We can't reuse the
    # target's title -- statham dedupes ObjectMeta by name and would then
    # rename the real definition. Instead, hand statham a unique synthetic
    # title; the SV serializer filters classes whose title ends with the
    # stub suffix out of the rendered output.
    title = stub_title_for(target_name)
    return {
        "type": "object",
        _AUTOTITLE: title,
        "title": title,
        _RECURSIVE_KEY: target_name,
    }


def is_stub_class_name(name: str) -> bool:
    return name.endswith(_STUB_SUFFIX)


def break_recursive_cycles(schema: Dict[str, Any]) -> int:
    """For each top-level definition, replace any in-place alias-to-self with a stub.

    Returns the number of replacements made (used by tests).
    """
    defs = schema.get("definitions") or {}
    replaced = 0
    for name, defn in defs.items():
        if name == _AUTOTITLE or not isinstance(defn, dict):
            continue
        replaced += _replace_aliases_in(defn, defn, name, {id(defn)})
    return replaced


def _replace_aliases_in(
    node: Any, target_def: Mapping[str, Any], target_name: str, in_path: Set[int]
) -> int:
    """Walk `node` and replace any sub-dict aliased to `target_def` with a stub."""
    if not isinstance(node, dict):
        return 0
    replaced = 0
    for key, val in list(node.items()):
        if isinstance(val, dict):
            if val is target_def:
                node[key] = _stub(target_name)
                replaced += 1
            elif id(val) not in in_path:
                in_path.add(id(val))
                replaced += _replace_aliases_in(val, target_def, target_name, in_path)
                in_path.discard(id(val))
        elif isinstance(val, list):
            for i, item in enumerate(val):
                if not isinstance(item, dict):
                    continue
                if item is target_def:
                    val[i] = _stub(target_name)
                    replaced += 1
                elif id(item) not in in_path:
                    in_path.add(id(item))
                    replaced += _replace_aliases_in(
                        item, target_def, target_name, in_path
                    )
                    in_path.discard(id(item))
    return replaced


def collect_recursive_refs(schema: Mapping[str, Any]) -> Dict[Tuple[str, str], str]:
    """Walk every property and record where a stub points back at a class.

    Keys mirror the bitvec / oneof side-tables: (owner_title, prop_name).
    Array items inherit their containing property's key (the SV side
    treats arrays uniformly with their element type).
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
            ref = target.get(_RECURSIVE_KEY)
            if isinstance(ref, str):
                out[(title, prop_name)] = ref
            visit(prop_schema, title)
        for name, child in (node.get("definitions") or {}).items():
            if name == _AUTOTITLE:
                continue
            visit(child, title)

    visit(schema, schema.get(_AUTOTITLE, schema.get("title", "")))
    return out
