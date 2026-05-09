"""Golden tests for the SV generator.

Each parametrised case runs ``app.py`` against a fixture schema and compares
the generated config_m.sv / testbench.sv against checked-in expected output.
Run with ``--update-golden`` to refresh the expected files in place.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


GENERATION_CASES = [
    # (case_name, schema_path_template_relative_to_repo)
    ("axi4", "examples/axi4_cfg_schema.json"),
    ("all_types", "tests/fixtures/all_types.json"),
]


def _run_generator(repo_root: Path, schema: Path, class_out: Path, tb_out: Path) -> None:
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
        ],
        cwd=repo_root,
        check=True,
    )


@pytest.mark.parametrize("case,schema_rel", GENERATION_CASES, ids=[c for c, _ in GENERATION_CASES])
def test_generation_matches_golden(
    case, schema_rel, repo_root, expected_dir, update_golden, tmp_path
):
    schema = repo_root / schema_rel
    class_out = tmp_path / "config_m.sv"
    tb_out = tmp_path / "testbench.sv"
    _run_generator(repo_root, schema, class_out, tb_out)

    expected_class = expected_dir / f"{case}.config_m.sv"
    expected_tb = expected_dir / f"{case}.testbench.sv"

    if update_golden:
        expected_dir.mkdir(parents=True, exist_ok=True)
        expected_class.write_text(class_out.read_text(encoding="utf8"), encoding="utf8")
        expected_tb.write_text(tb_out.read_text(encoding="utf8"), encoding="utf8")
        pytest.skip(f"goldens updated for {case}")

    assert (
        class_out.read_text(encoding="utf8") == expected_class.read_text(encoding="utf8")
    ), (
        f"{case} class generation drifted from {expected_class.relative_to(repo_root)}; "
        "rerun with --update-golden if the change is intended."
    )
    assert (
        tb_out.read_text(encoding="utf8") == expected_tb.read_text(encoding="utf8")
    ), (
        f"{case} testbench generation drifted from {expected_tb.relative_to(repo_root)}; "
        "rerun with --update-golden if the change is intended."
    )
