"""Shared pytest configuration.

Puts `src/` on sys.path so `from sv_json_schema.* import …` works whether
or not the project has been editable-installed. statham-schema is a real
PyPI dependency now, so no path manipulation is needed for it. Exposes
path fixtures and a simulator-detection fixture used by the end-to-end
tests.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
EXPECTED_DIR = Path(__file__).resolve().parent / "expected"

_SRC = REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--update-golden",
        action="store_true",
        default=False,
        help="Rewrite expected/* files from current generator output instead of comparing.",
    )


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture(scope="session")
def expected_dir() -> Path:
    return EXPECTED_DIR


@pytest.fixture(scope="session")
def update_golden(request: pytest.FixtureRequest) -> bool:
    return bool(request.config.getoption("--update-golden"))


@pytest.fixture(scope="session")
def simulator() -> str | None:
    """Return the simulator binary name on PATH, or None to skip e2e tests."""
    for name in ("vcs", "qrun"):
        if shutil.which(name):
            return name
    return None
