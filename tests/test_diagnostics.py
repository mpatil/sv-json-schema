"""Unit tests for serializers.diagnostics."""

from __future__ import annotations

import json as _json
import subprocess
import sys

import pytest

from serializers.diagnostics import collect_diagnostics


def _diags_for(node):
    return collect_diagnostics({"definitions": {"X": node}})


def _keywords(diags):
    return sorted({d.keyword for d in diags})


class TestCollectDiagnostics:
    def test_clean_schema_has_no_diagnostics(self):
        node = {
            "type": "object",
            "properties": {
                "a": {"type": "integer", "minimum": 0, "maximum": 10},
                "b": {"type": "string", "minLength": 1, "maxLength": 32},
                "c": {"type": "string", "format": "hex", "x-sv-width": 8},
            },
            "required": ["a"],
        }
        assert collect_diagnostics({"definitions": {"X": node}}) == []

    @pytest.mark.parametrize(
        "node,keyword",
        [
            ({"allOf": [{"type": "integer"}]}, "allOf"),
            ({"anyOf": [{"type": "integer"}]}, "anyOf"),
            ({"not": {"type": "integer"}}, "not"),
            ({"if": {}, "then": {}}, "if"),
            ({"type": "string", "pattern": "^.*"}, "pattern"),
            ({"type": "object", "patternProperties": {"^x_": {}}}, "patternProperties"),
            ({"type": "object", "dependencies": {"x": ["y"]}}, "dependencies"),
            ({"type": "object", "dependentRequired": {"x": ["y"]}}, "dependentRequired"),
            ({"type": "array", "contains": {}}, "contains"),
            ({"type": "object", "minProperties": 1}, "minProperties"),
            ({"type": "object", "maxProperties": 5}, "maxProperties"),
            ({"type": "object", "propertyNames": {}}, "propertyNames"),
            ({"type": "object", "unevaluatedProperties": False}, "unevaluatedProperties"),
        ],
    )
    def test_unsupported_keyword_is_flagged(self, node, keyword):
        diags = _diags_for(node)
        assert keyword in _keywords(diags), (
            f"expected `{keyword}` in diagnostics; got {_keywords(diags)}"
        )

    def test_additional_properties_as_schema_is_flagged(self):
        diags = _diags_for(
            {"type": "object", "additionalProperties": {"type": "integer"}}
        )
        assert "additionalProperties" in _keywords(diags)

    def test_additional_properties_false_is_not_flagged(self):
        diags = _diags_for(
            {
                "type": "object",
                "properties": {"a": {"type": "integer"}},
                "additionalProperties": False,
            }
        )
        assert _keywords(diags) == []

    def test_unsupported_string_format_is_flagged(self):
        diags = _diags_for({"type": "string", "format": "date-time"})
        assert "format" in _keywords(diags)

    def test_supported_string_formats_are_silent(self):
        for fmt in ("hex", "binary"):
            diags = _diags_for({"type": "string", "format": fmt})
            assert _keywords(diags) == [], f"`{fmt}` shouldn't warn (got {diags})"

    def test_unsupported_integer_format_is_flagged(self):
        diags = _diags_for({"type": "integer", "format": "uint64"})
        assert "format" in _keywords(diags)

    def test_int32_int64_are_silent(self):
        for fmt in ("int32", "int64"):
            diags = _diags_for({"type": "integer", "format": fmt})
            assert _keywords(diags) == [], f"`{fmt}` shouldn't warn"

    def test_multi_type_union_flagged(self):
        diags = _diags_for({"type": ["string", "null"]})
        assert "type" in _keywords(diags)

    def test_type_null_flagged(self):
        diags = _diags_for({"type": "null"})
        assert "type" in _keywords(diags)

    def test_diagnostic_path_uses_property_name(self):
        diags = collect_diagnostics(
            {
                "definitions": {
                    "X": {
                        "type": "object",
                        "properties": {"foo": {"type": "string", "pattern": "."}},
                    }
                }
            }
        )
        assert any(
            d.path.endswith("properties/foo") and d.keyword == "pattern"
            for d in diags
        )


class TestStrictCli:
    @pytest.fixture
    def bad_schema(self, tmp_path):
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Bad",
            "definitions": {
                "X": {
                    "type": "object",
                    "properties": {"a": {"type": "string", "pattern": "^.*"}},
                }
            },
        }
        path = tmp_path / "bad.json"
        path.write_text(_json.dumps(schema))
        return path

    def _run(self, repo_root, schema, *extra):
        return subprocess.run(
            [
                sys.executable,
                str(repo_root / "app.py"),
                "--input",
                str(schema),
                "--class-out",
                "/dev/null",
                "--tb-out",
                "/dev/null",
                *extra,
            ],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )

    def test_default_warns_and_succeeds(self, repo_root, bad_schema):
        result = self._run(repo_root, bad_schema)
        assert result.returncode == 0, result.stderr
        assert "warning" in result.stderr
        assert "pattern" in result.stderr

    def test_strict_errors_and_exits_nonzero(self, repo_root, bad_schema):
        result = self._run(repo_root, bad_schema, "--strict")
        assert result.returncode != 0
        assert "error" in result.stderr
        assert "pattern" in result.stderr


def test_existing_fixtures_have_zero_diagnostics(repo_root, fixtures_dir):
    """Every checked-in fixture should be diagnostics-clean.

    If something here starts to fire, either fix the fixture or update
    the diagnostics whitelist intentionally.
    """
    from json_ref_dict import RefDict, materialize
    from statham.titles import title_labeller

    from serializers.composition import apply_allof_merging

    schemas = [
        repo_root / "examples" / "axi4_cfg_schema.json",
        repo_root / "examples" / "types.json",
        fixtures_dir / "all_types.json",
        fixtures_dir / "with_oneof.json",
        fixtures_dir / "with_strict.json",
        fixtures_dir / "with_plain_enum.json",
        fixtures_dir / "with_validation.json",
        fixtures_dir / "with_allof.json",
    ]
    for schema in schemas:
        raw = materialize(
            RefDict.from_uri(f"{schema}#/"), context_labeller=title_labeller()
        )
        apply_allof_merging(raw)
        diags = collect_diagnostics(raw)
        assert diags == [], (
            f"{schema.name} has diagnostics:\n"
            + "\n".join("  " + d.format() for d in diags)
        )
