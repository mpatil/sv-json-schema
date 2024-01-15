from argparse import ArgumentParser, RawTextHelpFormatter
from contextlib import contextmanager
from logging import getLogger, INFO
from typing import Iterator, TextIO, Tuple
from sys import argv, stdout, path

from json_ref_dict import materialize, RefDict

from pathlib import Path

from mako import exceptions
from mako.template import Template

path.append("statham-schema")

from statham.schema.parser import parse
from serializers.sv_lang import serialize_sv
from statham.titles import title_labeller

from os import path

LOGGER = getLogger(__name__)
LOGGER.setLevel(INFO)


def parse_input_arg(input_arg: str) -> str:
    """Parse input URI as a valid JSON Schema ref.

    This tool accepts bare base URIs, without the JSON Pointer,
    so these should be converted to a root pointer.
    """
    if "#" not in input_arg:
        return input_arg + "#/"
    return input_arg


@contextmanager
def parse_args(args) -> Iterator[Tuple[str, TextIO]]:
    """Parse arguments, abstracting IO in a context manager."""

    parser = ArgumentParser(
        description="Generate statham models from JSON Schema files.",
        formatter_class=RawTextHelpFormatter,
        add_help=False,
    )
    required = parser.add_argument_group("Required arguments")
    required.add_argument(
        "--input",
        type=str,
        required=True,
        help="""Specify the path to the JSON Schema to be generated.

If the target schema is not at the root of a document, specify the
JSON Pointer in the same format as a JSON Schema `$ref`, e.g.
`--input path/to/document.json#/definitions/schema`

""",
    )
    required.add_argument(
        "--template",
        type=str,
        required=True,
        help="""
""",
    )
    optional = parser.add_argument_group("Optional arguments")
    optional.add_argument(
        "--output",
        type=str,
        default=None,
        help="""Output directory or file in which to write the output.

If the provided path is a directory, the command will derive the name
from the input argument. If not passed, the command will write to
stdout.

""",
    )
    optional.add_argument(
        "-h",
        "--help",
        action="help",
        help="Display this help message and exit.",
    )
    parsed = parser.parse_args(args)
    input_arg: str = parse_input_arg(parsed.input)
    template_arg: str = str(parsed.template)
    if parsed.output:
        if path.isdir(parsed.output):
            filename = ".".join(path.basename(parsed.input).split(".")[:-1])
            output_path = path.join(parsed.output, ".".join([filename, "py"]))
        else:
            output_path = parsed.output
        with open(output_path, "w", encoding="utf8") as file:
            yield input_arg, template_arg, file
        return
    yield input_arg, template_arg, stdout
    return


def main(input_uri: str) -> str:
    """Get a schema from a URI, and then return the generated python module.

    :param input_uri: URI of the target schema. This must follow the conventions
        of a JSON Schema ``"$ref"`` attribute.
    :return: Python module contents for generated models, as a string.
    """
    schema = materialize(
        RefDict.from_uri(input_uri), context_labeller=title_labeller()
    )
    return serialize_sv(*parse(schema))


def entry_point():
    """Entry point for command.

    Parse arguments, read from input and write to output.
    """
    with parse_args(argv[1:]) as (uri, tpl, output):
        in_tpl = Template(filename = str(tpl))
        try:
            output.write(in_tpl.render(params = main(uri)))
        except:
            print(exceptions.text_error_template().render())


if __name__ == "__main__":
    entry_point()
