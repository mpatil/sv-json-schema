"""Unit tests for serializers.composition (allOf property merging)."""

from __future__ import annotations

import pytest
from json_ref_dict import RefDict, materialize
from statham.titles import title_labeller

from serializers.composition import apply_allof_merging


class TestApplyAllOfMerging:
    def test_merges_branch_properties_into_parent(self):
        schema = {
            "definitions": {
                "Base": {
                    "type": "object",
                    "properties": {
                        "id":   {"type": "integer"},
                        "name": {"type": "string"},
                    },
                },
                "Cfg": {
                    "type": "object",
                    "allOf": [{
                        "type": "object",
                        "properties": {
                            "id":   {"type": "integer"},
                            "name": {"type": "string"},
                        },
                    }],
                    "properties": {"awuser": {"type": "integer"}},
                },
            }
        }
        merged = apply_allof_merging(schema)

        assert merged == 1
        cfg = schema["definitions"]["Cfg"]
        assert "allOf" not in cfg
        assert set(cfg["properties"].keys()) == {"id", "name", "awuser"}

    def test_merges_required_arrays_dedup(self):
        schema = {
            "definitions": {
                "Cfg": {
                    "type": "object",
                    "allOf": [{
                        "type": "object",
                        "properties": {"id": {"type": "integer"}},
                        "required": ["id"],
                    }],
                    "properties": {"x": {"type": "integer"}},
                    "required": ["x", "id"],
                }
            }
        }
        apply_allof_merging(schema)

        cfg = schema["definitions"]["Cfg"]
        # Order-preserving dedup: parent's existing entries first.
        assert cfg["required"] == ["x", "id"]

    def test_parent_properties_win_on_conflict(self):
        schema = {
            "definitions": {
                "Cfg": {
                    "type": "object",
                    "allOf": [{
                        "type": "object",
                        "properties": {
                            "x": {"type": "string", "default": "from_branch"}
                        },
                    }],
                    "properties": {
                        "x": {"type": "string", "default": "from_parent"}
                    },
                }
            }
        }
        apply_allof_merging(schema)

        # Parent's `x` definition is preserved; branch's is dropped.
        x = schema["definitions"]["Cfg"]["properties"]["x"]
        assert x["default"] == "from_parent"

    def test_non_object_branches_left_alone(self):
        schema = {
            "definitions": {
                "Tricky": {
                    "type": "integer",
                    "allOf": [
                        {"minimum": 0},
                        {"maximum": 10},
                    ],
                }
            }
        }
        merged = apply_allof_merging(schema)

        assert merged == 0
        # allOf still present so the diagnostic fires.
        assert "allOf" in schema["definitions"]["Tricky"]

    def test_mixed_branches_keep_unmergeable_ones(self):
        schema = {
            "definitions": {
                "Cfg": {
                    "type": "object",
                    "allOf": [
                        {
                            "type": "object",
                            "properties": {"id": {"type": "integer"}},
                        },
                        {"minProperties": 1},  # not an object branch
                    ],
                    "properties": {"x": {"type": "integer"}},
                }
            }
        }
        apply_allof_merging(schema)

        cfg = schema["definitions"]["Cfg"]
        # The object branch was merged...
        assert set(cfg["properties"].keys()) == {"id", "x"}
        # ...the non-object one is still there for diagnostics to flag.
        assert cfg["allOf"] == [{"minProperties": 1}]

    def test_no_allof_no_change(self):
        schema = {
            "definitions": {
                "Plain": {
                    "type": "object",
                    "properties": {"x": {"type": "integer"}},
                }
            }
        }
        merged = apply_allof_merging(schema)

        assert merged == 0
        assert schema["definitions"]["Plain"] == {
            "type": "object",
            "properties": {"x": {"type": "integer"}},
        }


def test_with_allof_fixture_merges_into_cfg(fixtures_dir):
    """End-to-end through materialize: the fixture's Cfg should pick up id/name."""
    raw = materialize(
        RefDict.from_uri(f"{fixtures_dir / 'with_allof.json'}#/"),
        context_labeller=title_labeller(),
    )
    apply_allof_merging(raw)

    cfg = raw["definitions"]["Cfg"]
    assert "allOf" not in cfg
    prop_names = {n for n in cfg["properties"].keys() if n != "_x_autotitle"}
    assert prop_names == {"id", "name", "awuser"}
    assert "id" in cfg["required"] and "awuser" in cfg["required"]
