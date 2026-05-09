"""Shared pytest configuration.

Puts the repo root and the bundled statham-schema submodule on sys.path so
test modules can `from serializers...` and `from statham...` directly without
relying on the user installing the project. Also exposes path fixtures and a
simulator-detection fixture used by the end-to-end tests.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
EXPECTED_DIR = Path(__file__).resolve().parent / "expected"

# Make the project + statham-schema importable for any test module.
for path in (REPO_ROOT, REPO_ROOT / "statham-schema"):
    p = str(path)
    if p not in sys.path:
        sys.path.insert(0, p)


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
