"""Unit tests for serializers.bitvec."""

from __future__ import annotations

import json

import pytest
from json_ref_dict import RefDict, materialize
from statham.titles import title_labeller

from serializers.bitvec import (
    BitVec,
    DEFAULT_BINARY_WIDTH,
    DEFAULT_HEX_WIDTH,
    RADIX_BINARY,
    RADIX_HEX,
    collect_bitvec_widths,
    register_format_validators,
)


def _materialised(path):
    return materialize(
        RefDict.from_uri(f"{path}#/"), context_labeller=title_labeller()
    )


class TestCollectWidths:
    def test_picks_up_hex_and_binary_with_explicit_width(self, fixtures_dir):
        raw = _materialised(fixtures_dir / "all_types.json")
        widths = collect_bitvec_widths(raw)

        assert widths[("AllTypes", "h")] == BitVec(RADIX_HEX, 16)
        assert widths[("AllTypes", "bn")] == BitVec(RADIX_BINARY, 4)

    def test_array_items_inherit_property_key(self, fixtures_dir):
        raw = _materialised(fixtures_dir / "all_types.json")
        widths = collect_bitvec_widths(raw)

        # h_arr is `array of hex` — bitvec metadata keyed by the property name,
        # not the (anonymous) item.
        assert widths[("AllTypes", "h_arr")] == BitVec(RADIX_HEX, 8)
        assert widths[("AllTypes", "bn_arr")] == BitVec(RADIX_BINARY, 2)

    def test_non_bitvec_strings_not_collected(self, fixtures_dir):
        raw = _materialised(fixtures_dir / "all_types.json")
        widths = collect_bitvec_widths(raw)

        assert ("AllTypes", "s") not in widths
        assert ("AllTypes", "s_arr") not in widths
        assert ("Inner", "tag") not in widths

    def test_default_widths_when_x_sv_width_omitted(self):
        schema = {
            "_x_autotitle": "Sample",
            "title": "Sample",
            "definitions": {
                "Sample": {
                    "_x_autotitle": "Sample",
                    "type": "object",
                    "properties": {
                        "h": {"type": "string", "format": "hex"},
                        "bn": {"type": "string", "format": "binary"},
                    },
                }
            },
        }
        widths = collect_bitvec_widths(schema)

        assert widths[("Sample", "h")] == BitVec(RADIX_HEX, DEFAULT_HEX_WIDTH)
        assert widths[("Sample", "bn")] == BitVec(RADIX_BINARY, DEFAULT_BINARY_WIDTH)

    def test_skips_autotitle_keys_inside_properties(self):
        schema = {
            "definitions": {
                "T": {
                    "_x_autotitle": "T",
                    "type": "object",
                    "properties": {
                        "_x_autotitle": "properties",
                        "h": {"type": "string", "format": "hex", "x-sv-width": 8},
                    },
                }
            }
        }
        widths = collect_bitvec_widths(schema)
        # Only the real prop is collected; the _x_autotitle marker is ignored.
        assert list(widths.keys()) == [("T", "h")]


class TestFormatValidators:
    @pytest.fixture(autouse=True)
    def _register(self):
        register_format_validators()

    def test_hex_accepts_canonical(self):
        from statham.schema.validation.format import format_checker

        assert format_checker(RADIX_HEX, "0xdeadbeef") is True
        assert format_checker(RADIX_HEX, "deadbeef") is True
        assert format_checker(RADIX_HEX, "0X12") is True

    def test_hex_rejects_garbage(self):
        from statham.schema.validation.format import format_checker

        assert format_checker(RADIX_HEX, "0xZZ") is False
        assert format_checker(RADIX_HEX, "") is False

    def test_binary_accepts_canonical(self):
        from statham.schema.validation.format import format_checker

        assert format_checker(RADIX_BINARY, "0b1010") is True
        assert format_checker(RADIX_BINARY, "1010") is True

    def test_binary_rejects_non_bits(self):
        from statham.schema.validation.format import format_checker

        assert format_checker(RADIX_BINARY, "0b1012") is False
        assert format_checker(RADIX_BINARY, "0xab") is False
        assert format_checker(RADIX_BINARY, "") is False
