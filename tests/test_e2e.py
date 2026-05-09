"""End-to-end tests: generate SV, compile + run, inspect outputs.

Skipped automatically when neither vcs nor qrun is on PATH. The tests run
``make`` from the repo root and inspect / mutate files in-place; the
``clean_workspace`` fixture wipes build products before and after each test
to keep the tree tidy and the data fixtures restore any input files they
mutate.
"""

from __future__ import annotations

import json
import subprocess
import sys

import pytest


_TIMEOUT_SECONDS = 300


def _make_target(simulator: str) -> str:
    return "vcsrun" if simulator == "vcs" else "run"


def _make(repo_root, target):
    return subprocess.run(
        ["make", target],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=_TIMEOUT_SECONDS,
    )


@pytest.fixture
def clean_workspace(repo_root):
    """Wipe generated artifacts before and after each test."""
    subprocess.run(["make", "clean"], cwd=repo_root, capture_output=True, text=True)
    yield
    subprocess.run(["make", "clean"], cwd=repo_root, capture_output=True, text=True)


@pytest.fixture
def addrmap_input(repo_root):
    """Backup/restore the AddrMap input file around a mutating test."""
    p = repo_root / "examples" / "data" / "AddrMap.json"
    saved = p.read_text(encoding="utf8")
    yield p
    p.write_text(saved, encoding="utf8")


def _require_simulator(simulator):
    if simulator is None:
        pytest.skip("no simulator (vcs/qrun) on PATH")


def test_axi4_addrmap_roundtrip(simulator, repo_root, clean_workspace):
    """Every key in the AddrMap input JSON should re-appear with the same value."""
    _require_simulator(simulator)
    result = _make(repo_root, _make_target(simulator))
    assert result.returncode == 0, f"sim failed: {result.stdout}\n{result.stderr}"

    inputs = json.loads(
        (repo_root / "examples" / "data" / "AddrMap.json").read_text(encoding="utf8")
    )[0]
    output = json.loads((repo_root / "AddrMap0.json").read_text(encoding="utf8"))

    for key, value in inputs.items():
        assert output[key] == value, (
            f"AddrMap.{key} did not round-trip: input={value!r} output={output.get(key)!r}"
        )


def test_required_field_missing_emits_uvm_error(
    simulator, repo_root, addrmap_input, clean_workspace
):
    """Stripping a required field should fire the uvm_error guard at runtime."""
    _require_simulator(simulator)
    data = json.loads(addrmap_input.read_text(encoding="utf8"))
    data[0].pop("addr")
    addrmap_input.write_text(json.dumps(data, indent=2), encoding="utf8")

    result = _make(repo_root, _make_target(simulator))
    combined = result.stdout + result.stderr
    assert 'required field "addr" missing' in combined, (
        f"expected required-field uvm_error not in sim output:\n{combined}"
    )


# ---------------------------------------------------------------------------
# oneOf
# ---------------------------------------------------------------------------


def _generate(repo_root, schema, class_out, tb_out, data_dir):
    subprocess.run(
        [
            sys.executable,
            str(repo_root / "app.py"),
            "--input",
            str(schema),
            "--class-out",
            str(class_out),
            "--tb-out",
            str(tb_out),
            "--tb-data-dir",
            str(data_dir),
        ],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )


def _vcs_compile_and_run(workspace):
    subprocess.run(
        [
            "vcs",
            "-full64",
            "-sverilog",
            "-ntb_opts",
            "uvm-1.2",
            "-timescale=1ns/1ps",
            "-f",
            "sv_tb.f",
            "testbench.sv",
        ],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
        timeout=_TIMEOUT_SECONDS,
    )
    return subprocess.run(
        ["./simv", "+UVM_VERBOSITY=UVM_MEDIUM", "+vcs+lic+wait"],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
        timeout=_TIMEOUT_SECONDS,
    )


def _build_workspace(repo_root, fixtures_dir, schema_name, tmp_path, data_dir):
    """Generate SV from a fixture into tmp_path with runtime deps symlinked in."""
    _generate(
        repo_root=repo_root,
        schema=fixtures_dir / schema_name,
        class_out=tmp_path / "config_m.sv",
        tb_out=tmp_path / "testbench.sv",
        data_dir=data_dir,
    )
    for name in ("sv-embed-json", "serializers", "sv_tb.f"):
        (tmp_path / name).symlink_to(repo_root / name)
    return tmp_path


def test_oneof_roundtrip_dispatches_by_discriminator(
    simulator, repo_root, fixtures_dir, tmp_path
):
    """Generated factory must pick the right concrete subclass per discriminator."""
    if simulator != "vcs":
        pytest.skip("oneOf e2e currently requires vcs")

    data_dir = fixtures_dir / "data"
    workspace = _build_workspace(
        repo_root, fixtures_dir, "with_oneof.json", tmp_path, data_dir
    )
    _vcs_compile_and_run(workspace)

    cfg0 = json.loads((workspace / "Cfg0.json").read_text(encoding="utf8"))
    cfg1 = json.loads((workspace / "Cfg1.json").read_text(encoding="utf8"))

    # First record exercises the "addr" branch.
    assert cfg0["name"] == "as_addr"
    assert cfg0["map"]["kind"] == "addr"
    assert cfg0["map"]["size"] == 4096
    assert cfg0["map"]["region"] == "0xdeadbeef"

    # Second record exercises the "reg" branch via the same field.
    assert cfg1["name"] == "as_reg"
    assert cfg1["map"]["kind"] == "reg"
    assert cfg1["map"]["offset"] == 17


def test_strict_clean_input_passes(
    simulator, repo_root, fixtures_dir, tmp_path
):
    """A Strict-class input that contains exactly the declared keys should not error."""
    if simulator != "vcs":
        pytest.skip("strict e2e currently requires vcs")
    workspace = _build_workspace(
        repo_root, fixtures_dir, "with_strict.json", tmp_path, fixtures_dir / "data"
    )
    sim = _vcs_compile_and_run(workspace)
    combined = sim.stdout + sim.stderr
    assert "additionalProperties: false" not in combined, (
        f"unexpected additionalProperties uvm_error on clean input:\n{combined}"
    )


def test_strict_extra_key_emits_uvm_error(
    simulator, repo_root, fixtures_dir, tmp_path
):
    """An extra key not in the schema must fire the additionalProperties guard."""
    if simulator != "vcs":
        pytest.skip("strict e2e currently requires vcs")
    rogue = tmp_path / "rogue_data"
    rogue.mkdir()
    (rogue / "Strict.json").write_text(
        json.dumps([{"a": 1, "b": "ok", "rogue_extra": 99}], indent=2)
    )
    (rogue / "Loose.json").write_text(
        (fixtures_dir / "data" / "Loose.json").read_text(encoding="utf8")
    )
    workspace = _build_workspace(
        repo_root, fixtures_dir, "with_strict.json", tmp_path / "ws", rogue
    )
    sim = _vcs_compile_and_run(workspace)
    combined = sim.stdout + sim.stderr
    assert "unexpected property 'rogue_extra'" in combined, (
        f"expected additionalProperties uvm_error not in sim output:\n{combined}"
    )


def test_plain_enum_roundtrip(simulator, repo_root, fixtures_dir, tmp_path):
    """Plain string + integer enums (scalar and array) must round-trip."""
    if simulator != "vcs":
        pytest.skip("plain-enum e2e currently requires vcs")
    workspace = _build_workspace(
        repo_root,
        fixtures_dir,
        "with_plain_enum.json",
        tmp_path,
        fixtures_dir / "data_plain_enum",
    )
    _vcs_compile_and_run(workspace)
    out = json.loads((workspace / "Cfg0.json").read_text(encoding="utf8"))
    expected = json.loads(
        (fixtures_dir / "data_plain_enum" / "Cfg.json").read_text(encoding="utf8")
    )[0]
    assert out["color"] == expected["color"]
    assert out["level"] == expected["level"]
    assert out["tags"] == expected["tags"]
    assert out["vals"] == expected["vals"]


def test_plain_enum_int_out_of_set_emits_uvm_error(
    simulator, repo_root, fixtures_dir, tmp_path
):
    """An integer-enum value not in the allowed set must fire uvm_error."""
    if simulator != "vcs":
        pytest.skip("plain-enum e2e currently requires vcs")
    rogue = tmp_path / "rogue_data"
    rogue.mkdir()
    (rogue / "Cfg.json").write_text(
        json.dumps(
            [{"color": "red", "level": 99, "tags": ["a"], "vals": [1]}], indent=2
        )
    )
    workspace = _build_workspace(
        repo_root, fixtures_dir, "with_plain_enum.json", tmp_path / "ws", rogue
    )
    sim = _vcs_compile_and_run(workspace)
    combined = sim.stdout + sim.stderr
    assert "'level' value 99 not in enum" in combined, (
        f"expected enum_int uvm_error not in sim output:\n{combined}"
    )


def _run_validation_case(repo_root, fixtures_dir, tmp_path, cfg_payload):
    """Run the with_validation fixture against `cfg_payload`; return combined sim output."""
    rogue = tmp_path / "data"
    rogue.mkdir()
    (rogue / "Cfg.json").write_text(json.dumps(cfg_payload, indent=2))
    workspace = _build_workspace(
        repo_root, fixtures_dir, "with_validation.json", tmp_path / "ws", rogue
    )
    sim = _vcs_compile_and_run(workspace)
    return sim.stdout + sim.stderr


def test_validation_clean_input_passes(
    simulator, repo_root, fixtures_dir, tmp_path
):
    if simulator != "vcs":
        pytest.skip("validation e2e currently requires vcs")
    out = _run_validation_case(
        repo_root, fixtures_dir, tmp_path,
        [{"name": "okay", "tag": "v1", "version": 1}],
    )
    for unexpected in ("must equal const", "below minLength", "above maxLength"):
        assert unexpected not in out, (
            f"clean input should not produce a {unexpected!r} uvm_error:\n{out}"
        )


def test_validation_const_mismatch_string_emits_error(
    simulator, repo_root, fixtures_dir, tmp_path
):
    if simulator != "vcs":
        pytest.skip("validation e2e currently requires vcs")
    out = _run_validation_case(
        repo_root, fixtures_dir, tmp_path,
        [{"name": "okay", "tag": "wrong", "version": 1}],
    )
    assert "'tag' must equal const" in out, (
        f"expected const-mismatch uvm_error not in sim output:\n{out}"
    )


def test_validation_minlength_violation_emits_error(
    simulator, repo_root, fixtures_dir, tmp_path
):
    if simulator != "vcs":
        pytest.skip("validation e2e currently requires vcs")
    out = _run_validation_case(
        repo_root, fixtures_dir, tmp_path,
        [{"name": "ok", "tag": "v1", "version": 1}],  # 2 chars, minLength=3
    )
    assert "below minLength 3" in out, (
        f"expected minLength uvm_error not in sim output:\n{out}"
    )


def test_validation_maxlength_violation_emits_error(
    simulator, repo_root, fixtures_dir, tmp_path
):
    if simulator != "vcs":
        pytest.skip("validation e2e currently requires vcs")
    out = _run_validation_case(
        repo_root, fixtures_dir, tmp_path,
        [{"name": "wayyytooooLONG", "tag": "v1", "version": 1}],  # 14 > 8
    )
    assert "above maxLength 8" in out, (
        f"expected maxLength uvm_error not in sim output:\n{out}"
    )


def test_allof_merged_properties_roundtrip(
    simulator, repo_root, fixtures_dir, tmp_path
):
    """Properties merged via allOf must round-trip alongside native ones."""
    if simulator != "vcs":
        pytest.skip("allOf e2e currently requires vcs")
    workspace = _build_workspace(
        repo_root,
        fixtures_dir,
        "with_allof.json",
        tmp_path,
        fixtures_dir / "data_allof",
    )
    _vcs_compile_and_run(workspace)
    out = json.loads((workspace / "Cfg0.json").read_text(encoding="utf8"))
    inp = json.loads(
        (fixtures_dir / "data_allof" / "Cfg.json").read_text(encoding="utf8")
    )[0]
    # `awuser` was native; `id`/`name` came in via allOf from Identifiable.
    for key in ("id", "name", "awuser"):
        assert out[key] == inp[key], (
            f"Cfg.{key} did not round-trip: in={inp[key]!r} out={out.get(key)!r}"
        )


def test_int64_roundtrip(simulator, repo_root, fixtures_dir, tmp_path):
    """An integer with format=int64 must round-trip values beyond 2^31."""
    if simulator != "vcs":
        pytest.skip("int64 e2e currently requires vcs")
    workspace = _build_workspace(
        repo_root, fixtures_dir, "all_types.json", tmp_path, fixtures_dir / "data"
    )
    _vcs_compile_and_run(workspace)
    out = json.loads((workspace / "AllTypes0.json").read_text(encoding="utf8"))
    inp = json.loads((fixtures_dir / "data" / "AllTypes.json").read_text(encoding="utf8"))[0]
    assert out["i64"] == inp["i64"] == 9999999999
    assert out["i64_arr"] == inp["i64_arr"] == [12345678901, 9999999999]


def test_oneof_unknown_discriminator_emits_uvm_error(
    simulator, repo_root, fixtures_dir, tmp_path
):
    """An unknown discriminator value should fire the factory's uvm_error."""
    if simulator != "vcs":
        pytest.skip("oneOf e2e currently requires vcs")

    # Build a parallel data dir whose Cfg.json has a bogus `kind` value.
    rogue_data_dir = tmp_path / "rogue_data"
    rogue_data_dir.mkdir()
    bogus = [
        {
            "name": "bogus",
            "map": {"kind": "rocket", "size": 1, "offset": 1},
        }
    ]
    (rogue_data_dir / "Cfg.json").write_text(json.dumps(bogus, indent=2))
    (rogue_data_dir / "AddrMap.json").write_text(
        (fixtures_dir / "data" / "AddrMap.json").read_text(encoding="utf8")
    )
    (rogue_data_dir / "RegMap.json").write_text(
        (fixtures_dir / "data" / "RegMap.json").read_text(encoding="utf8")
    )

    workspace = _build_workspace(
        repo_root, fixtures_dir, "with_oneof.json", tmp_path / "ws", rogue_data_dir
    )
    sim = _vcs_compile_and_run(workspace)
    assert "unknown kind: rocket" in (sim.stdout + sim.stderr), (
        f"expected oneOf uvm_error not in sim output:\n{sim.stdout}\n{sim.stderr}"
    )
