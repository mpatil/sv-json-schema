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
