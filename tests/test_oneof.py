"""Unit tests for serializers.oneof."""

from __future__ import annotations

import pytest
from json_ref_dict import RefDict, materialize
from statham.titles import title_labeller

from sv_json_schema.oneof import (
    OneOfBranch,
    OneOfError,
    OneOfSpec,
    collect_oneof_props,
    collect_oneofs,
)


@pytest.fixture(scope="module")
def with_oneof_raw(fixtures_dir):
    return materialize(
        RefDict.from_uri(f"{fixtures_dir / 'with_oneof.json'}#/"),
        context_labeller=title_labeller(),
    )


class TestCollectOneofs:
    def test_picks_up_anymap(self, with_oneof_raw):
        oneofs = collect_oneofs(with_oneof_raw)
        assert "AnyMap" in oneofs

    def test_branches_carry_discriminator_values_from_defaults(self, with_oneof_raw):
        spec = collect_oneofs(with_oneof_raw)["AnyMap"]
        assert spec.discriminator == "kind"
        assert spec.branches == (
            OneOfBranch("AddrMap", "addr"),
            OneOfBranch("RegMap", "reg"),
        )

    def test_no_oneof_returns_empty(self):
        assert collect_oneofs({}) == {}
        assert (
            collect_oneofs({"definitions": {"X": {"type": "object", "properties": {}}}})
            == {}
        )

    def test_missing_discriminator_raises(self):
        schema = {
            "definitions": {
                "Bad": {
                    "oneOf": [
                        {"type": "object", "properties": {"k": {"type": "string", "default": "a"}}},
                        {"type": "object", "properties": {"k": {"type": "string", "default": "b"}}},
                    ]
                }
            }
        }
        with pytest.raises(OneOfError, match="discriminator"):
            collect_oneofs(schema)

    def test_branch_missing_discriminator_default_raises(self):
        schema = {
            "definitions": {
                "Bad": {
                    "oneOf": [
                        {"type": "object", "_x_autotitle": "Branch1", "properties": {"k": {"type": "string", "default": "a"}}},
                        {"type": "object", "_x_autotitle": "Branch2", "properties": {"k": {"type": "string"}}},
                    ],
                    "discriminator": {"propertyName": "k"}
                }
            }
        }
        with pytest.raises(OneOfError, match="default"):
            collect_oneofs(schema)


class TestCollectOneofProps:
    def test_cfg_map_points_at_anymap(self, with_oneof_raw):
        props = collect_oneof_props(with_oneof_raw)
        assert props == {("Cfg", "map"): "AnyMap"}

    def test_no_oneof_returns_empty(self):
        assert collect_oneof_props({}) == {}
