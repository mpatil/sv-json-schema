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
                                          serializers.sv_lang.serialize_sv
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
| `$ref` (intra-document and external file)                 | done |
| recursive `$ref`, `null`, multi-type union, `pattern`     | not yet — see `TODO.md` |

## References

1. [statham-schema](https://github.com/jacksmith15/statham-schema) — JSON Schema parser
1. [sv-embed-json](https://github.com/mpatil/sv-embed-json) — SV runtime JSON parser
1. [JSON Schema](https://json-schema.org/)

## Development

1. Clone the repository: `git clone https://github.com/mpatil/sv-json-schema.git && cd sv-json-schema`
1. Initialise git submodules: `git submodule update --init --recursive`
1. Install the requirements: `pip install -r requirements.txt`
1. Setup simulator env. Mentor Questa (`qrun`) and Synopsys VCS are supported.
1. Run the default generation with Questa: `make`
1. Or run with VCS: `make vcsrun`

The default `make` target generates against `examples/axi4_cfg_schema.json`;
override the example with `make EXAMPLE=other_schema_basename`.

## Tests

* `make test` — full pytest run (unit + golden + end-to-end). The end-to-end
  tests are skipped automatically when no simulator is on `PATH`.
* `make test-fast` — unit and golden tests only; no simulator required.
* `make update-golden` — refresh `tests/expected/*.config_m.sv` and
  `*.testbench.sv` after an intentional generator change.

The full layout under `tests/` is described in `docs/FEATURES.md` — every
supported feature has a corresponding fixture in `tests/fixtures/`.
