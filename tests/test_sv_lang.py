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

from sv_json_schema.bitvec import collect_bitvec_widths
from sv_json_schema.intformat import collect_int_formats
from sv_json_schema.oneof import collect_oneof_props, collect_oneofs
from sv_json_schema.sv_lang import serialize_sv


@pytest.fixture(scope="module")
def all_types_params(fixtures_dir):
    raw = materialize(
        RefDict.from_uri(f"{fixtures_dir / 'all_types.json'}#/"),
        context_labeller=title_labeller(),
    )
    widths = collect_bitvec_widths(raw)
    int_formats = collect_int_formats(raw)
    return serialize_sv(parse(raw), widths, int_formats=int_formats)


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


@pytest.fixture(scope="module")
def with_strict_params(fixtures_dir):
    raw = materialize(
        RefDict.from_uri(f"{fixtures_dir / 'with_strict.json'}#/"),
        context_labeller=title_labeller(),
    )
    return serialize_sv(parse(raw))


@pytest.fixture(scope="module")
def with_plain_enum_params(fixtures_dir):
    raw = materialize(
        RefDict.from_uri(f"{fixtures_dir / 'with_plain_enum.json'}#/"),
        context_labeller=title_labeller(),
    )
    return serialize_sv(parse(raw))


@pytest.fixture(scope="module")
def with_validation_params(fixtures_dir):
    raw = materialize(
        RefDict.from_uri(f"{fixtures_dir / 'with_validation.json'}#/"),
        context_labeller=title_labeller(),
    )
    return serialize_sv(parse(raw))


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
            ("i64", "int", "longint", False),
            ("i64_arr", "int_array", "longint", True),
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

    def test_exclusive_min_max_constraints(self, all_types_params):
        props = _props_by_name(all_types_params["classes"]["AllTypes"])
        assert props["i_excl"]["rangeConstraints"] == [
            "m_i_excl > 0",
            "m_i_excl < 100",
        ]

    def test_multiple_of_constraint(self, all_types_params):
        props = _props_by_name(all_types_params["classes"]["AllTypes"])
        assert props["i_mult"]["rangeConstraints"] == ["m_i_mult % 4 == 0"]

    def test_unique_items_constraint(self, all_types_params):
        props = _props_by_name(all_types_params["classes"]["AllTypes"])
        assert props["uniq_arr"]["uniqueItems"] is True
        # Non-unique array should report False.
        assert props["i_arr"]["uniqueItems"] is False

    def test_scalar_props_have_no_unique(self, all_types_params):
        props = _props_by_name(all_types_params["classes"]["AllTypes"])
        # A scalar (non-array) field should never get uniqueItems=True.
        assert props["i"]["uniqueItems"] is False

    @pytest.mark.parametrize("name,bits", [("i", 32), ("i64", 64), ("i64_arr", 64)])
    def test_integer_format_sets_print_bits(self, all_types_params, name, bits):
        props = _props_by_name(all_types_params["classes"]["AllTypes"])
        assert props[name]["bits"] == bits

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


class TestStrictSection:
    def test_strict_class_marked(self, with_strict_params):
        assert with_strict_params["classes"]["Strict"]["strict"] is True

    def test_loose_class_not_marked(self, with_strict_params):
        assert with_strict_params["classes"]["Loose"]["strict"] is False


class TestPlainEnum:
    def test_string_enum_typedef_emitted(self, with_plain_enum_params):
        # Synthesised typedef gets registered alongside object-with-enum typedefs.
        assert with_plain_enum_params["enums"]["Cfg_color_e"] == ["red", "green", "blue"]
        assert with_plain_enum_params["enums"]["Cfg_tags_e"] == ["a", "b"]

    def test_string_enum_property_dispatches_via_existing_enum_path(
        self, with_plain_enum_params
    ):
        props = _props_by_name(with_plain_enum_params["classes"]["Cfg"])
        assert props["color"]["type_cat"] == "enum"
        assert props["color"]["type"] == "Cfg_color_e"
        assert props["tags"]["type_cat"] == "enum_array"
        assert props["tags"]["type"] == "Cfg_tags_e"

    def test_int_enum_keeps_int_storage_with_inside_set(self, with_plain_enum_params):
        props = _props_by_name(with_plain_enum_params["classes"]["Cfg"])
        assert props["level"]["type_cat"] == "enum_int"
        assert props["level"]["type"] == "int"
        assert props["level"]["enumIntValues"] == [0, 1, 5]
        assert props["vals"]["type_cat"] == "enum_int_array"
        assert props["vals"]["type"] == "int"
        assert props["vals"]["enumIntValues"] == [1, 2, 3]

    def test_string_enum_default_emitted_as_bareword(self, with_plain_enum_params):
        props = _props_by_name(with_plain_enum_params["classes"]["Cfg"])
        # Plain-string-enum default must NOT be quoted; it's an enum identifier.
        assert props["color"]["def"] == "red"


class TestValidationChecks:
    def test_minlength_maxlength_emit_uvm_error_snippets(self, with_validation_params):
        props = _props_by_name(with_validation_params["classes"]["Cfg"])
        checks = props["name"]["validationChecks"]
        assert any("len() < 3" in c and "minLength 3" in c for c in checks)
        assert any("len() > 8" in c and "maxLength 8" in c for c in checks)

    def test_const_string_emits_check_and_default(self, with_validation_params):
        props = _props_by_name(with_validation_params["classes"]["Cfg"])
        prop = props["tag"]
        assert any('m_tag != "v1"' in c for c in prop["validationChecks"])
        # `const` promotes to the field's default literal.
        assert prop["def"] == '"v1"'

    def test_const_integer_emits_check_and_default(self, with_validation_params):
        props = _props_by_name(with_validation_params["classes"]["Cfg"])
        prop = props["version"]
        assert any("m_version != 1" in c for c in prop["validationChecks"])
        assert prop["def"] == "1"


def test_invalid_string_enum_value_raises(fixtures_dir, tmp_path):
    """An enum value that isn't a valid SV identifier should fail at codegen."""
    import json as _json

    from sv_json_schema.sv_lang import PlainEnumError

    bad = tmp_path / "bad_enum.json"
    bad.write_text(
        _json.dumps(
            {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "Bad",
                "definitions": {
                    "Cfg": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "string", "enum": ["foo-bar"]}
                        },
                    }
                },
            }
        )
    )
    raw = materialize(
        RefDict.from_uri(f"{bad}#/"), context_labeller=title_labeller()
    )
    with pytest.raises(PlainEnumError, match="foo-bar"):
        serialize_sv(parse(raw))
