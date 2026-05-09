"""Generate SystemVerilog config classes and a UVM testbench from a JSON Schema."""

import os
import sys
from argparse import ArgumentParser, RawTextHelpFormatter
from pathlib import Path
from typing import Iterable, Tuple

from json_ref_dict import RefDict, materialize
from mako import exceptions
from mako.template import Template

# statham-schema is consumed via the submodule rather than from PyPI; expose
# the package on sys.path before importing.
_REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_REPO_ROOT / "statham-schema"))

from statham.schema.parser import parse  # noqa: E402
from statham.titles import title_labeller  # noqa: E402

from serializers.bitvec import (  # noqa: E402
    collect_bitvec_widths,
    register_format_validators,
)
from serializers.composition import apply_allof_merging  # noqa: E402
from serializers.diagnostics import collect_diagnostics  # noqa: E402
from serializers.intformat import collect_int_formats  # noqa: E402
from serializers.oneof import collect_oneof_props, collect_oneofs  # noqa: E402
from serializers.recursive import (  # noqa: E402
    break_recursive_cycles,
    collect_recursive_refs,
)
from serializers.sv_lang import serialize_sv  # noqa: E402


_DEFAULT_CLASS_TEMPLATE = _REPO_ROOT / "serializers" / "sv_lang.mako"
_DEFAULT_TB_TEMPLATE = _REPO_ROOT / "examples" / "sv_lang_tb.mako"


def parse_input_arg(input_arg: str) -> str:
    """Convert a bare base URI into a full JSON Schema ref (root pointer)."""
    return input_arg if "#" in input_arg else input_arg + "#/"


def _parse_args(argv: Iterable[str]):
    parser = ArgumentParser(
        description=__doc__,
        formatter_class=RawTextHelpFormatter,
    )
    parser.add_argument(
        "--input",
        required=True,
        help=(
            "Path to the JSON Schema. To target a sub-schema, append a JSON\n"
            "Pointer fragment, e.g. path/to/document.json#/definitions/Schema"
        ),
    )
    parser.add_argument(
        "--class-out",
        type=Path,
        help="Output path for the generated SV class (default: stdout when no outputs given).",
    )
    parser.add_argument(
        "--tb-out",
        type=Path,
        help="Output path for the generated UVM testbench.",
    )
    parser.add_argument(
        "--class-template",
        type=Path,
        default=_DEFAULT_CLASS_TEMPLATE,
        help="Override the SV class Mako template.",
    )
    parser.add_argument(
        "--tb-template",
        type=Path,
        default=_DEFAULT_TB_TEMPLATE,
        help="Override the UVM testbench Mako template.",
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
            "warns about JSON-Schema keywords it doesn't honor (e.g., allOf, "
            "pattern) and proceeds; with --strict it exits non-zero before "
            "writing any output."
        ),
    )
    # Backwards-compatible single-output mode used by older invocations.
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
    return parser.parse_args(list(argv))


def _resolve_schema(input_uri: str, *, strict: bool):
    """Materialise the JSON Schema, returning (parsed elements, side-tables).

    statham's `parse` mutates the schema dict, so non-statham metadata
    (bit-vector widths, oneOf groups + their property usages) is harvested
    first. Diagnostics are also computed before parsing so the path strings
    reflect the input shape.
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


def _write(target, contents: str) -> None:
    if target is None:
        sys.stdout.write(contents)
    else:
        target = Path(target)
        if target.is_dir():
            raise SystemExit(
                f"--output target {target} is a directory; pass a file path"
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(contents, encoding="utf8")


def main(argv: Iterable[str] = None) -> int:
    register_format_validators()
    args = _parse_args(sys.argv[1:] if argv is None else argv)

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
        # No outputs requested → render the class to stdout (matches old default).
        sys.stdout.write(_render(args.class_template, params))
        return 0

    if args.class_out is not None:
        _write(args.class_out, _render(args.class_template, params))
    if args.tb_out is not None:
        _write(args.tb_out, _render(args.tb_template, params))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
