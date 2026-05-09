"""`allOf` composition support: pre-parse property-merging.

statham doesn't flatten `allOf` for us — it would otherwise be a separate
`AllOf(*subschemas)` composition element that the SV serializer doesn't know
how to render. For object-shaped compositions (the common "mix in this
property set" pattern), we can merge the branches' `properties` and
`required` into the parent definition before parsing, then strip the
`allOf` key so neither statham nor the diagnostics pass complain.

Branches that aren't simple object schemas (composing constraints on a
primitive type, nested allOf chains, etc.) are left untouched so they
still surface as a diagnostic.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping


_AUTOTITLE = "_x_autotitle"


def _is_object_branch(node: Any) -> bool:
    """A branch we know how to merge: object schema with `properties`."""
    return (
        isinstance(node, dict)
        and node.get("type") == "object"
        and isinstance(node.get("properties"), dict)
    )


def _merge_into(target: Dict[str, Any], branch: Mapping[str, Any]) -> None:
    """Fold a single object branch's properties and required into target."""
    target_props: Dict[str, Any] = target.setdefault("properties", {})
    for prop_name, prop_schema in (branch.get("properties") or {}).items():
        if prop_name == _AUTOTITLE:
            continue
        # Parent-defined properties win on conflict; we only fill in gaps.
        target_props.setdefault(prop_name, prop_schema)

    branch_required = branch.get("required") or []
    if branch_required:
        target_required: List[str] = target.setdefault("required", [])
        for name in branch_required:
            if name not in target_required:
                target_required.append(name)


def apply_allof_merging(schema: Dict[str, Any]) -> int:
    """Walk top-level `definitions` and merge every object-shaped allOf.

    Returns the count of definitions that had at least one allOf branch
    merged (used by tests).
    """
    merged = 0
    for name, node in (schema.get("definitions") or {}).items():
        if name == _AUTOTITLE or not isinstance(node, dict):
            continue
        if not _merge_node(node):
            continue
        merged += 1
    return merged


def _merge_node(node: Dict[str, Any]) -> bool:
    """Merge mergeable allOf branches in `node`. Returns True if any merged."""
    branches = node.get("allOf")
    if not isinstance(branches, list):
        return False
    leftover: List[Any] = []
    merged_any = False
    for branch in branches:
        if _is_object_branch(branch):
            _merge_into(node, branch)
            merged_any = True
        else:
            leftover.append(branch)
    if not merged_any:
        return False
    if leftover:
        # Some branches couldn't be merged; keep them so the diagnostics pass
        # surfaces them and the user knows the composition is still partial.
        node["allOf"] = leftover
    else:
        del node["allOf"]
    return True
