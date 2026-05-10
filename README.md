![](https://img.shields.io/badge/license-MIT-green)

# sv-json-schema

Generate SystemVerilog (UVM-style) configuration classes from JSON
Schema. Each generated class can:

* deserialize an input JSON file into typed members (`fromJSON`)
* serialize itself back to JSON (`toJSON`)
* be randomized under the constraints declared in the schema

The same schema validates fine via any third-party JSON-Schema validator
(Python `jsonschema`, ajv, ...) — anything the generator can't model is
flagged as a diagnostic and `--strict` turns those into hard errors at
codegen time, so generation and validation stay in lockstep.

## Quick example

Schema (`my_schema.json`):

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "definitions": {
    "Cfg": {
      "type": "object",
      "description": "Channel configuration.",
      "properties": {
        "id":    {"type": "integer", "minimum": 0, "maximum": 255},
        "addr":  {"type": "string", "format": "hex", "x-sv-width": 32, "default": "0x0"},
        "kind":  {"type": "string", "enum": ["read", "write"]}
      },
      "required": ["id", "kind"],
      "additionalProperties": false
    }
  }
}
```

Generated SV (excerpt):

```sv
typedef enum { read, write } Cfg_kind_e;
typedef uvm_enum_wrapper#(Cfg_kind_e) Cfg_kind_e_wrapper;

class Cfg extends uvm_object;
    `uvm_object_utils(Cfg)

    // Channel configuration.
    rand int               m_id;
    rand logic [32-1:0]    m_addr = 'h0;
    rand Cfg_kind_e        m_kind;

    constraint id_range_c { m_id >= 0; m_id <= 255; };

    virtual function void fromJSON(Val_ jv);
        if (jv.getByKey("id") == null)
          `uvm_error(get_full_name(), "required field \"id\" missing from input")
        `from_json_int(m_id, id)
        `from_json_hex(m_addr, addr)
        if (jv.getByKey("kind") == null)
          `uvm_error(get_full_name(), "required field \"kind\" missing from input")
        `from_json_enum(m_kind, kind, Cfg_kind_e)
        // additionalProperties: false -- reject unknown keys
        ...
    endfunction
    ...
endclass
```

The generator handles the schema-side bookkeeping; the
[sv-embed-json](https://github.com/mpatil/sv-embed-json) library handles
runtime JSON parsing on the SV side. See
[`docs/FEATURES.md`](docs/FEATURES.md) for the full schema → SV mapping
table and a fixture pointer for every supported construct.

## Install

The project ships as a Python package at `src/sv_json_schema/` with a
[PEP 517](https://peps.python.org/pep-0517/) build backend. There is no
`setup.py`; the metadata, dependencies, and console-script entry point
all live in [`pyproject.toml`](pyproject.toml). Modern pip (≥ 21) reads
that directly.

```sh
git clone https://github.com/mpatil/sv-json-schema.git
cd sv-json-schema
git submodule update --init --recursive             # pulls sv-embed-json
pip install -e '.[test]'                            # editable install + pytest
```

That installs:

* `sv-json-schema` console script (entry point: `sv_json_schema.cli:main`)
* the package data — `sv_lang.mako`, `sv_lang_tb.mako`, and the SV
  runtime helper `sv_tb_pkg.sv` — under `sv_json_schema/data/`
* runtime deps from PyPI: `Mako`, `json-ref-dict`, `statham-schema>=0.15.1`
* dev deps from the `[test]` extra: `pytest`

To build a wheel:

```sh
pip install build
python -m build --wheel       # writes dist/sv_json_schema-<version>-py3-none-any.whl
```

If you'd rather not install at all, every `python3 app.py …` command
keeps working — `app.py` is a thin shim that puts `src/` on `sys.path`
and forwards to `sv_json_schema.cli.main`.

### Why no `setup.py`?

`pyproject.toml` with `setuptools.build_meta` is the supported way for
setuptools projects post-PEP 517. The old `setup.py` is no longer
required and packaging tooling (pip, build, hatch) reads `pyproject.toml`
directly. If you have an older pip (`< 21`), upgrade with
`pip install --upgrade pip` first.

## Use

```sh
# Generate a config class + testbench from a schema
sv-json-schema \
    --input examples/axi4_cfg_schema.json \
    --class-out config_m.sv \
    --tb-out testbench.sv \
    --tb-data-dir examples/data

# Locate the bundled SV runtime (sv_tb_pkg.sv + default templates) so
# your simulator's `+incdir+` list can pick them up.
sv-json-schema --print-incdir

# Treat any unsupported-keyword diagnostic as a hard error
sv-json-schema --strict --input my.json --class-out … --tb-out …
```

Flags worth knowing:

| Flag | What it does |
|------|---|
| `--input`            | path to the schema (with optional `#/...` JSON-Pointer fragment) |
| `--class-out`        | output path for `config_m.sv` |
| `--tb-out`           | output path for `testbench.sv` |
| `--tb-data-dir`      | directory the generated testbench reads input JSON from (defaults to `examples/data`) |
| `--class-template`   | override the bundled `sv_lang.mako` |
| `--tb-template`      | override the bundled `sv_lang_tb.mako` |
| `--strict`           | turn keyword-drop warnings into errors |
| `--print-incdir`     | print the path to the bundled `data/` (useful for `+incdir+`) |

## Run

The simulator-driven flows live in the `Makefile`:

```sh
make                      # qrun (Mentor Questa)
make vcsrun               # Synopsys VCS
make EXAMPLE=types vcsrun # alternate schema under examples/<EXAMPLE>.json
```

The Makefile's `SV_JSON_SCHEMA` variable is `python3 app.py` by default
(works without `pip install`). After an editable install, swap to
`sv-json-schema` for the same effect.

`sv_tb.f` already lists the right include paths:

```
+incdir+sv-embed-json/src
+incdir+sv-embed-json/src/json
+incdir+sv-embed-json/src/json/uvm
+incdir+src/sv_json_schema/data
```

## Tests

```sh
make test         # pytest: unit + golden + end-to-end (e2e auto-skipped without a sim)
make test-fast    # unit + golden only; no simulator required
make update-golden  # refresh tests/expected/* after an intentional generator change
```

Every supported schema construct has a fixture under `tests/fixtures/`
and a checked-in golden output under `tests/expected/`. New features land
with: a fixture, a golden, a unit test on the serializer's params dict,
and an e2e test that round-trips a sample input through VCS.

## Architecture

```
                           +-------------------------+
schema.json --(json_ref_dict)→| resolved schema dict |
                           +-----------+-------------+
                                       |
                                       v   pre-parse passes (mutate / harvest)
                            apply_allof_merging
                            break_recursive_cycles
                            collect_diagnostics  (warns or, with --strict, errors)
                            collect_bitvec_widths
                            collect_oneofs / collect_oneof_props
                            collect_int_formats
                            collect_recursive_refs
                                       |
                                       v
                                statham.parse → typed Element tree
                                       |
                                       v
                          sv_json_schema.sv_lang.serialize_sv
                                       |
                                       v
                                  Mako params dict
                                       |
                                       v
                       sv_lang.mako, sv_lang_tb.mako
                                       |
                                       v
                       config_m.sv, testbench.sv
```

The runtime SV side (`Val_` tree, parsers, `mkInt`/`mkStr`/...
constructors, plus the optional UVM macro layer) lives in
[sv-embed-json](https://github.com/mpatil/sv-embed-json) and is consumed
via the submodule.

## Features at a glance

For each construct see [`docs/FEATURES.md`](docs/FEATURES.md) for input
→ SV examples and the test fixture that exercises it.

| JSON Schema construct                                         | Status |
|---------------------------------------------------------------|--------|
| `string`, `integer`, `number`, `boolean`, `object`, `array`   | done |
| Integer `format: "int64"` → SV `longint` (`int32` honored)    | done |
| `default`                                                     | done |
| `required` (uvm_error on missing key)                         | done |
| `const` (string / integer / boolean)                          | done |
| `format: "hex"` / `format: "binary"` + `x-sv-width: N`        | done |
| object-with-enum (statham idiom)                              | done |
| plain `enum` on string and integer                            | done |
| `minimum`, `maximum`, `exclusiveMinimum`, `exclusiveMaximum`, `multipleOf` | done |
| `minLength`, `maxLength`                                      | done |
| `minItems`, `maxItems`, `uniqueItems`                         | done |
| `additionalProperties: false`                                 | done |
| `oneOf` (top-level definition, with `discriminator`)          | done |
| `allOf` (object property-merging from referenced bases)       | done |
| Recursive `$ref` (self-referential schemas)                   | done |
| `$ref` (intra-document and external file)                     | done |
| `description` propagated to SV `//` comments                  | done |
| `--strict` diagnostics for unsupported standard keywords      | done |
| `null`, multi-type union, `pattern`, `not`, `anyOf`, `if/then/else` | not yet — see [`TODO.md`](TODO.md) |

## References

* [sv-embed-json](https://github.com/mpatil/sv-embed-json) — SV runtime JSON parser (the `Val_` tree + UVM macro layer)
* [statham-schema](https://github.com/jacksmith15/statham-schema) — Python JSON Schema parser (PyPI, draft 4–7)
* [JSON Schema](https://json-schema.org/) — spec
