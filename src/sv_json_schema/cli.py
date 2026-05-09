"""CLI entry point.

`sv-json-schema --input schema.json --class-out config_m.sv --tb-out tb.sv`

Bundled defaults for the Mako templates and the SV runtime helper file
(`sv_tb_pkg.sv`) live under `sv_json_schema/data/` and ship with the wheel.
`sv-json-schema print-incdir` prints that directory so users can hand it
to their simulator's `+incdir+` list and pick up `sv_tb_pkg.sv`.
"""

from __future__ import annotations

import sys
from argparse import ArgumentParser, RawTextHelpFormatter
from importlib import resources
from pathlib import Path
from typing import Iterable, Optional

from json_ref_dict import RefDict, materialize
from mako import exceptions
from mako.template import Template
from statham.schema.parser import parse
from statham.titles import title_labeller

from sv_json_schema.bitvec import collect_bitvec_widths, register_format_validators
from sv_json_schema.composition import apply_allof_merging
from sv_json_schema.diagnostics import collect_diagnostics
from sv_json_schema.intformat import collect_int_formats
from sv_json_schema.oneof import collect_oneof_props, collect_oneofs
from sv_json_schema.recursive import break_recursive_cycles, collect_recursive_refs
from sv_json_schema.sv_lang import serialize_sv


def _data_dir() -> Path:
    """Return the path to the bundled data directory (templates + sv_tb_pkg.sv)."""
    return Path(str(resources.files("sv_json_schema") / "data"))


def parse_input_arg(input_arg: str) -> str:
    """Convert a bare base URI into a full JSON Schema ref (root pointer)."""
    return input_arg if "#" in input_arg else input_arg + "#/"


def _build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog="sv-json-schema",
        description=__doc__,
        formatter_class=RawTextHelpFormatter,
    )
    parser.add_argument(
        "--input",
        help=(
            "Path to the JSON Schema. To target a sub-schema, append a JSON\n"
            "Pointer fragment, e.g. path/to/document.json#/definitions/Schema."
        ),
    )
    parser.add_argument(
        "--class-out",
        type=Path,
        help="Output path for the generated SV class.",
    )
    parser.add_argument(
        "--tb-out",
        type=Path,
        help="Output path for the generated UVM testbench.",
    )
    parser.add_argument(
        "--class-template",
        type=Path,
        default=None,
        help="Override the SV class Mako template (defaults to the bundled one).",
    )
    parser.add_argument(
        "--tb-template",
        type=Path,
        default=None,
        help="Override the UVM testbench Mako template (defaults to the bundled one).",
    )
    parser.add_argument(
        "--tb-data-dir",
        default="examples/data",
        help="Directory the generated testbench reads input JSON files from.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Treat schema diagnostics as errors. Without --strict the generator "
            "warns about JSON-Schema keywords it doesn't honor and proceeds; "
            "with --strict it exits non-zero before writing any output."
        ),
    )
    parser.add_argument(
        "--print-incdir",
        action="store_true",
        help=(
            "Print the path to the bundled SV data directory (containing\n"
            "`sv_tb_pkg.sv` and the default Mako templates) and exit. Use\n"
            "with `+incdir+$(sv-json-schema --print-incdir)` in your simulator\n"
            "Makefile to find sv_tb_pkg.sv from the wheel install."
        ),
    )
    # Backwards-compatible single-output mode kept for callers who passed
    # --template / --output prior to the dual-output split.
    parser.add_argument(
        "--template",
        type=Path,
        help="Single template to render. Pairs with --output.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output for --template.",
    )
    return parser


def _resolve_schema(input_uri: str, *, strict: bool):
    """Materialise the schema and harvest every side-table before parse.

    statham's `parse` mutates the schema dict (and raises on cycles), so all
    of: allOf merging, recursive-ref cycle breaking, diagnostics collection,
    and the bit-vector / oneOf / int-format / recursive-ref side-tables
    happen first.
    """
    raw = materialize(
        RefDict.from_uri(input_uri), context_labeller=title_labeller()
    )
    apply_allof_merging(raw)
    break_recursive_cycles(raw)
    diagnostics = collect_diagnostics(raw)
    for d in diagnostics:
        sys.stderr.write(f"{'error' if strict else 'warning'}: {d.format()}\n")
    if strict and diagnostics:
        raise SystemExit(
            f"--strict: {len(diagnostics)} unsupported-keyword diagnostic(s); "
            "aborting before generation."
        )
    widths = collect_bitvec_widths(raw)
    oneofs = collect_oneofs(raw)
    oneof_props = collect_oneof_props(raw)
    int_formats = collect_int_formats(raw)
    recursive_refs = collect_recursive_refs(raw)
    return parse(raw), widths, oneofs, oneof_props, int_formats, recursive_refs


def _render(template_path: Path, params: dict) -> str:
    try:
        return Template(filename=str(template_path)).render(params=params)
    except Exception:
        sys.stderr.write(exceptions.text_error_template().render())
        raise


def _write(target: Optional[Path], contents: str) -> None:
    if target is None:
        sys.stdout.write(contents)
        return
    target = Path(target)
    if target.is_dir():
        raise SystemExit(
            f"--output target {target} is a directory; pass a file path"
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(contents, encoding="utf8")


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = _build_parser().parse_args(
        sys.argv[1:] if argv is None else list(argv)
    )

    if args.print_incdir:
        sys.stdout.write(str(_data_dir()) + "\n")
        return 0

    if not args.input:
        sys.stderr.write("error: --input is required (or pass --print-incdir)\n")
        return 2

    register_format_validators()

    data_dir = _data_dir()
    class_template = args.class_template or (data_dir / "sv_lang.mako")
    tb_template = args.tb_template or (data_dir / "sv_lang_tb.mako")

    (
        elements, widths, oneofs, oneof_props, int_formats, recursive_refs
    ) = _resolve_schema(parse_input_arg(args.input), strict=args.strict)
    params = serialize_sv(
        elements, widths, oneofs, oneof_props, int_formats, recursive_refs
    )
    params["data_dir"] = args.tb_data_dir.rstrip("/")

    if args.template is not None:
        _write(args.output, _render(args.template, params))
        return 0

    if args.class_out is None and args.tb_out is None:
        sys.stdout.write(_render(class_template, params))
        return 0

    if args.class_out is not None:
        _write(args.class_out, _render(class_template, params))
    if args.tb_out is not None:
        _write(args.tb_out, _render(tb_template, params))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
