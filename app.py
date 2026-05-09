"""Backwards-compatibility shim.

The generator was reorganized into a real Python package at
`src/sv_json_schema/`. This file forwards `python3 app.py …` to
`sv_json_schema.cli.main()` so the existing Makefile / scripts keep
working without edits while users migrate to the proper CLI:

    sv-json-schema --input … --class-out … --tb-out …
    python3 -m sv_json_schema --input … --class-out … --tb-out …
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make the package importable when running directly from the repo without
# `pip install -e .`.
_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from sv_json_schema.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
