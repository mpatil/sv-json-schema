"""Unit tests for serializers.sv_lang.

These drive the real statham parser against a small synthetic schema fixture
so the assertions exercise the end-to-end path that ``app.py`` takes,
without involving Mako or the simulator.
"""

from __future__ import annotations

import pytest
from json_ref_dict import RefDict, materialize
from statham.schema.parser import parse
from statham.titles import title_labeller

from serializers.bitvec import collect_bitvec_widths
from serializers.oneof import collect_oneof_props, collect_oneofs
from serializers.sv_lang import serialize_sv


@pytest.fixture(scope="module")
def all_types_params(fixtures_dir):
    raw = materialize(
        RefDict.from_uri(f"{fixtures_dir / 'all_types.json'}#/"),
        context_labeller=title_labeller(),
    )
    widths = collect_bitvec_widths(raw)
    return serialize_sv(parse(raw), widths)


@pytest.fixture(scope="module")
def with_oneof_params(fixtures_dir):
    raw = materialize(
        RefDict.from_uri(f"{fixtures_dir / 'with_oneof.json'}#/"),
        context_labeller=title_labeller(),
    )
    widths = collect_bitvec_widths(raw)
    oneofs = collect_oneofs(raw)
    oneof_props = collect_oneof_props(raw)
    return serialize_sv(parse(raw), widths, oneofs, oneof_props)


def _props_by_name(class_dict):
    """Index a class entry's member list by property name."""
    return {p["name"]: p for p in class_dict["members"]}


class TestEnumSection:
    def test_mode_enum_values(self, all_types_params):
        assert all_types_params["enums"]["Mode"] == ["M_OFF=0", "M_ON=1"]


class TestClassesSection:
    def test_all_expected_classes_emitted(self, all_types_params):
        # Mode is an enum so it's not a class.
        assert set(all_types_params["classes"].keys()) == {"Inner", "AllTypes"}

    def test_inner_required_is_marked(self, all_types_params):
        props = _props_by_name(all_types_params["classes"]["Inner"])
        assert props["tag"]["isRequired"] is True
        assert props["n"]["isRequired"] is False

    @pytest.mark.parametrize(
        "name,type_cat,sv_type,is_array",
        [
            ("i", "int", "int", False),
            ("i_arr", "int_array", "int", True),
            ("b", "bool", "bit", False),
            ("b_arr", "bool_array", "bit", True),
            ("s", "string", "string", False),
            ("s_arr", "string_array", "string", True),
            ("h", "hex", "logic", False),
            ("h_arr", "hex_array", "logic", True),
            ("bn", "binary", "logic", False),
            ("bn_arr", "binary_array", "logic", True),
            ("e", "enum", "Mode", False),
            ("obj", "object", "Inner", False),
            ("obj_arr", "object_array", "Inner", True),
        ],
    )
    def test_property_dispatch(
        self, all_types_params, name, type_cat, sv_type, is_array
    ):
        props = _props_by_name(all_types_params["classes"]["AllTypes"])
        prop = props[name]
        assert prop["type_cat"] == type_cat
        assert prop["type"] == sv_type
        assert prop["isArray"] is is_array

    @pytest.mark.parametrize(
        "name,expected_width",
        [("h", 16), ("h_arr", 8), ("bn", 4), ("bn_arr", 2)],
    )
    def test_bitvec_widths_propagate(self, all_types_params, name, expected_width):
        props = _props_by_name(all_types_params["classes"]["AllTypes"])
        assert props[name]["width"] == expected_width

    @pytest.mark.parametrize(
        "name",
        ["i", "b", "b_arr", "s", "s_arr", "obj_arr", "e"],
    )
    def test_non_bitvec_width_is_none(self, all_types_params, name):
        props = _props_by_name(all_types_params["classes"]["AllTypes"])
        assert props[name]["width"] is None

    def test_required_set(self, all_types_params):
        props = _props_by_name(all_types_params["classes"]["AllTypes"])
        required = {n for n, p in props.items() if p["isRequired"]}
        assert required == {"i", "h", "obj"}

    def test_array_size_constraints(self, all_types_params):
        props = _props_by_name(all_types_params["classes"]["AllTypes"])
        assert props["i_arr"]["minItems"] == 1
        assert props["i_arr"]["maxItems"] == 4

    def test_defaults_passed_through(self, all_types_params):
        props = _props_by_name(all_types_params["classes"]["AllTypes"])
        assert props["i"]["def"] == "0"
        assert props["b"]["def"] == "0"
        assert props["s"]["def"] == '"default"'
        assert props["h"]["def"] == "'h0"
        assert props["bn"]["def"] == "'b0000"


class TestOneOfSection:
    def test_anymap_in_oneofs(self, with_oneof_params):
        oneofs = with_oneof_params["oneOfs"]
        assert "AnyMap" in oneofs
        assert oneofs["AnyMap"]["discriminator"] == "kind"
        branches = {b["name"]: b["value"] for b in oneofs["AnyMap"]["branches"]}
        assert branches == {"AddrMap": "addr", "RegMap": "reg"}

    def test_branches_extend_base(self, with_oneof_params):
        cs = with_oneof_params["classes"]
        assert cs["AddrMap"]["extends"] == "AnyMap"
        assert cs["RegMap"]["extends"] == "AnyMap"
        # Cfg is a regular class — not a branch.
        assert cs["Cfg"]["extends"] == "uvm_object"

    def test_cfg_map_is_oneof_typed(self, with_oneof_params):
        props = _props_by_name(with_oneof_params["classes"]["Cfg"])
        assert props["map"]["type_cat"] == "oneof"
        assert props["map"]["type"] == "AnyMap"
        assert props["map"]["oneOfBase"] == "AnyMap"
        assert props["map"]["isRand"] is False

    def test_anymap_not_in_classes(self, with_oneof_params):
        # Base classes live in `oneOfs`; only concrete classes go in `classes`.
        assert "AnyMap" not in with_oneof_params["classes"]
