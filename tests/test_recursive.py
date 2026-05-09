"""Unit tests for serializers.recursive."""

from __future__ import annotations

from json_ref_dict import RefDict, materialize
from statham.titles import title_labeller

from serializers.recursive import (
    break_recursive_cycles,
    collect_recursive_refs,
    is_stub_class_name,
    stub_title_for,
)


class TestBreakRecursiveCycles:
    def test_self_alias_via_array_replaced(self):
        # Build a small cyclic dict by hand (no $ref, just shared identity).
        tree = {
            "type": "object",
            "_x_autotitle": "Tree",
            "properties": {
                "value": {"type": "integer"},
                "children": {"type": "array", "items": None},
            },
        }
        tree["properties"]["children"]["items"] = tree
        schema = {"definitions": {"Tree": tree}}

        replaced = break_recursive_cycles(schema)
        assert replaced == 1

        items = schema["definitions"]["Tree"]["properties"]["children"]["items"]
        assert items["x-sv-recursive-ref"] == "Tree"
        # Real definition still has its own properties.
        assert "value" in schema["definitions"]["Tree"]["properties"]

    def test_no_cycles_returns_zero(self):
        schema = {
            "definitions": {
                "Plain": {
                    "type": "object",
                    "properties": {"x": {"type": "integer"}},
                }
            }
        }
        assert break_recursive_cycles(schema) == 0
        assert (
            "x-sv-recursive-ref"
            not in schema["definitions"]["Plain"]["properties"]["x"]
        )

    def test_self_alias_via_property_replaced(self):
        node = {
            "type": "object",
            "_x_autotitle": "Node",
            "properties": {"parent": None},
        }
        node["properties"]["parent"] = node
        schema = {"definitions": {"Node": node}}

        replaced = break_recursive_cycles(schema)
        assert replaced == 1
        parent = schema["definitions"]["Node"]["properties"]["parent"]
        assert parent["x-sv-recursive-ref"] == "Node"

    def test_with_recursive_fixture_breaks_cycle(self, fixtures_dir):
        raw = materialize(
            RefDict.from_uri(f"{fixtures_dir / 'with_recursive.json'}#/"),
            context_labeller=title_labeller(),
        )
        # The materialized dict is cyclic.
        assert (
            raw["definitions"]["Tree"]["properties"]["children"]["items"]
            is raw["definitions"]["Tree"]
        )
        replaced = break_recursive_cycles(raw)
        assert replaced == 1
        # After breaking, the items entry is a stub, not the same dict.
        assert (
            raw["definitions"]["Tree"]["properties"]["children"]["items"]
            is not raw["definitions"]["Tree"]
        )
        assert (
            raw["definitions"]["Tree"]["properties"]["children"]["items"][
                "x-sv-recursive-ref"
            ]
            == "Tree"
        )


class TestCollectRecursiveRefs:
    def test_records_owner_and_target(self, fixtures_dir):
        raw = materialize(
            RefDict.from_uri(f"{fixtures_dir / 'with_recursive.json'}#/"),
            context_labeller=title_labeller(),
        )
        break_recursive_cycles(raw)
        refs = collect_recursive_refs(raw)
        assert refs == {("Tree", "children"): "Tree"}

    def test_no_recursive_returns_empty(self):
        assert collect_recursive_refs({}) == {}


class TestStubTitle:
    def test_round_trip_with_known_suffix(self):
        title = stub_title_for("Tree")
        assert title.endswith("RecStub")
        assert is_stub_class_name(title)

    def test_non_stub_titles_not_matched(self):
        for n in ("Tree", "Cfg", "AddrMap", "Identifiable"):
            assert not is_stub_class_name(n)
