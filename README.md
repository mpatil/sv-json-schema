![](https://img.shields.io/badge/license-MIT-green)

# sv-json-schema

Generate SystemVerilog configuration classes (UVM-based) from JSON Schema.
Each generated class can:

* deserialize an input JSON file into typed members (`fromJSON`)
* serialize itself back to JSON (`toJSON`)
* be randomized under the constraints declared in the schema

## How it fits together

```
                                  +-------------------------+
schema.json  --(json_ref_dict)--> | resolved schema dict    |
                                  +-----------+-------------+
                                              |
                                              v
                            +-------------------------------+
                            | side-tables harvested before  |
                            | statham mutates the dict:     |
                            |   - bit-vector widths         |
                            |   - oneOf bases + branches    |
                            +-----------+-------------------+
                                        |
                                        v        +-------------------+
                            statham.parse  ----> | typed Element tree|
                                                 +---------+---------+
                                                           |
                                                           v
                                          sv_json_schema.sv_lang.serialize_sv
                                                           |
                                                           v
                                                  +--------+--------+
                                                  | params for Mako |
                                                  +--------+--------+
                                                           |
                            sv_lang.mako, sv_lang_tb.mako  |
                                                           v
                                                config_m.sv, testbench.sv
```

The runtime SV side uses [sv-embed-json](https://github.com/mpatil/sv-embed-json)
for parsing JSON files into a `Val_` tree.

## Features at a glance

For each construct, see [`docs/FEATURES.md`](docs/FEATURES.md) for input → SV
output examples and the test fixture that exercises it.

| JSON Schema construct                                     | Status |
|-----------------------------------------------------------|--------|
| `string`, `integer`, `number`, `boolean`, `object`, `array` | done |
| Integer `format: "int64"` → SV `longint` (and explicit `int32`) | done |
| `default`                                                 | done |
| `required` (uvm_error on missing key)                     | done |
| `const` (string / integer / boolean)                      | done |
| `format: "hex"` / `format: "binary"` + `x-sv-width: N`    | done |
| object-with-enum (statham idiom)                          | done |
| plain `enum` on string                                    | done |
| plain `enum` on integer                                   | done |
| `minimum`, `maximum`                                      | done |
| `exclusiveMinimum`, `exclusiveMaximum`, `multipleOf`      | done |
| `minLength`, `maxLength`                                  | done |
| `minItems`, `maxItems`, `uniqueItems`                     | done |
| `additionalProperties: false`                             | done |
| `oneOf` (top-level definition, with `discriminator`)      | done |
| `allOf` (object property-merging from referenced bases)   | done |
| Recursive `$ref` (self-referential schemas)               | done |
| `$ref` (intra-document and external file)                 | done |
| `description` propagated to SV `//` comments              | done |
| `--strict` diagnostics for unsupported standard keywords  | done |
| `null`, multi-type union, `pattern`                       | not yet — see `TODO.md` |

## References

1. [statham-schema](https://github.com/jacksmith15/statham-schema) — JSON Schema parser
1. [sv-embed-json](https://github.com/mpatil/sv-embed-json) — SV runtime JSON parser
1. [JSON Schema](https://json-schema.org/)

## Install

The Python generator is packaged at `src/sv_json_schema/`. The SV runtime
that the generated code depends on lives in the
[sv-embed-json](https://github.com/mpatil/sv-embed-json) submodule.

```sh
git clone https://github.com/mpatil/sv-json-schema.git
cd sv-json-schema
git submodule update --init --recursive            # pulls sv-embed-json
pip install -e .[test]                             # editable install + pytest
```

That gives you the `sv-json-schema` console script and pulls
`statham-schema`, `Mako`, and `json-ref-dict` from PyPI.

## Use

```sh
# Generate a config class + testbench from a schema
sv-json-schema --input examples/axi4_cfg_schema.json \
               --class-out config_m.sv --tb-out testbench.sv \
               --tb-data-dir examples/data

# Locate the bundled SV runtime (sv_tb_pkg.sv + default templates)
sv-json-schema --print-incdir
```

`--print-incdir` returns the directory the wheel installs to (or the
in-tree `src/sv_json_schema/data/` for editable installs); add it to your
simulator's `+incdir+` list so SV picks up `sv_tb_pkg.sv`.

`--strict` turns warnings on unsupported standard JSON-Schema keywords
into hard errors.

## Build

The default `make` target uses `app.py` (a thin shim that puts `src/`
on `sys.path`) so a fresh clone runs without `pip install`:

```sh
make             # qrun (Mentor Questa)
make vcsrun      # Synopsys VCS
make EXAMPLE=types vcsrun      # alternate schema under examples/
```

After `pip install -e .` the same flow works via `sv-json-schema` directly;
the Makefile's `SV_JSON_SCHEMA = python3 app.py` is just a default, swap
for `sv-json-schema` if you prefer.

## Tests

* `make test` — full pytest run (unit + golden + end-to-end). The end-to-end
  tests are skipped automatically when no simulator is on `PATH`.
* `make test-fast` — unit and golden tests only; no simulator required.
* `make update-golden` — refresh `tests/expected/*.config_m.sv` and
  `*.testbench.sv` after an intentional generator change.

The full layout under `tests/` is described in `docs/FEATURES.md` — every
supported feature has a corresponding fixture in `tests/fixtures/`.
