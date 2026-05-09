# Supported features

One section per JSON Schema construct that the generator handles, with the
input shape, the generated SystemVerilog, and a pointer to the fixture in
`tests/fixtures/` that exercises it. The construct **not** listed here is, by
construction, not implemented; see `TODO.md` for the status of every gap.

The "fixture" pointer lets the docs and the tests stay in lockstep — every
section maps to a checked-in schema + golden output + e2e test.

---

## Primitive types

| JSON type   | SV mapping                       | Notes                          |
|-------------|----------------------------------|--------------------------------|
| `string`    | `string m_x;`                    | Not `rand` by default.         |
| `integer`   | `rand int m_x;`                  | Use `format: "int64"` for 64-bit. |
| `number`    | `real m_x;`                      |                                |
| `boolean`   | `rand bit m_x;`                  | 0/1.                           |
| `object`    | nested generated class           |                                |
| `array`     | dynamic array `m_x[]` of inner   |                                |

`null` and multi-type unions (`["string", "null"]`) are **not** supported.

### Integer width via `format`

Statham strips `format` from numeric elements during parsing, so the keyword
is harvested from the resolved schema dict (see `serializers/intformat.py`)
before parse, in the same pattern as `bitvec`/`oneof`.

```json
{ "type": "integer", "format": "int64" }
{ "type": "integer", "format": "int32" }
```

```sv
rand longint m_long_field;     // 64-bit
rand int     m_short_field;    // 32-bit (default)
```

The full 64-bit value round-trips through fromJSON/toJSON; sv-embed-json's
parser uses `$sscanf("%d", longint)` so values beyond 2^31 are preserved
end to end. UVM's `print_field_int` is invoked with `bits=64` for `longint`
properties and `bits=32` for `int`.

Fixture: `tests/fixtures/all_types.json` (`i64`, `i64_arr`).

---

## Defaults

`default` becomes the SV initializer:

```json
{ "type": "integer", "default": 7 }
```

```sv
rand int m_x = 7;
```

If no `default` is given but `const` is, `const` is promoted to default
(see [const](#const)).

Fixture: `tests/fixtures/all_types.json`.

---

## `required` enforcement

Required fields generate a missing-key check at the top of `fromJSON`:

```json
{ "type": "object",
  "properties": {"addr": {"type": "string", "format": "hex", "x-sv-width": 32}},
  "required": ["addr"] }
```

```sv
virtual function void fromJSON(Val_ jv);
    if (jv.getByKey("addr") == null)
      `uvm_error(get_full_name(), "required field \"addr\" missing from input")
    `from_json_hex(addr)
endfunction
```

Fixture: `examples/axi4_cfg_schema.json` (the AddrMap definition has
`required: ["addr", "size"]`).

---

## `const`

A scalar property pinned to a single value. Generated as both a default
literal **and** a runtime mismatch check.

```json
{ "type": "string", "const": "v1" }
```

```sv
string m_tag = "v1";
// ... in fromJSON, after `from_json_string(tag)`:
if (m_tag != "v1")
  `uvm_error(get_full_name(), $sformatf("'tag' must equal const %s, got '%s'", "v1", m_tag))
```

Supported on `string`, `integer`, `boolean`. Fixture:
`tests/fixtures/with_validation.json`.

---

## Bit vectors: `format: "hex"` / `format: "binary"` + `x-sv-width`

Hex- and binary-formatted strings become SV bit vectors of a declared width.
The radix lives in `format`; the width lives in the vendor keyword
`x-sv-width` (statham strips unknown kwargs, so the width is harvested from
the resolved schema dict before parsing — see `serializers/bitvec.py`).

```json
{ "type": "string", "format": "hex",    "x-sv-width": 32, "default": "0x0" }
{ "type": "string", "format": "binary", "x-sv-width": 4,  "default": "0b0000" }
```

```sv
rand logic [32-1:0] m_addr = 'h0;
rand logic [4-1:0]  m_mode = 'b0000;
// fromJSON:
`from_json_hex(addr)
`from_json_binary(mode)
// toJSON dumps "0x..." / "0b..." strings.
```

Width defaults to 32 bits if `x-sv-width` is omitted. Fixtures:
`examples/axi4_cfg_schema.json`, `tests/fixtures/all_types.json`.

---

## Enums

Three flavors:

### Object-with-enum (statham idiom)

A definition typed as `object` with an `enum: { NAME: value, ... }` map.
Becomes an SV `typedef enum` with the named values, plus a
`uvm_enum_wrapper`.

```json
"AddrMapKind": { "type": "object", "enum": {"NORMAL": 0, "STRIPE": null} }
```

```sv
typedef enum { NORMAL=0, STRIPE } AddrMapKind;
typedef uvm_enum_wrapper#(AddrMapKind) AddrMapKind_wrapper;
```

Fixture: `examples/axi4_cfg_schema.json` (AddrMapKind, AddrMapDomain, etc.).

### Plain string enum

Standard JSON-Schema enum on a string field. Generates an SV typedef named
`${ClassName}_${PropName}_e` with the JSON values used **verbatim** as enum
identifiers.

Constraint: each enum value must be a valid SV identifier
(`[A-Za-z_][A-Za-z0-9_]*`); otherwise the generator raises `PlainEnumError`.

```json
{ "type": "string", "enum": ["red", "green", "blue"], "default": "red" }
```

```sv
typedef enum { red, green, blue } Cfg_color_e;
typedef uvm_enum_wrapper#(Cfg_color_e) Cfg_color_e_wrapper;
rand Cfg_color_e m_color = red;
```

Fixture: `tests/fixtures/with_plain_enum.json`.

### Plain integer enum

Standard JSON-Schema enum on an integer field. Stays an `int` field with an
inside-set constraint and a runtime check.

```json
{ "type": "integer", "enum": [0, 1, 5] }
```

```sv
rand int m_level;
constraint level_enum_c { m_level inside { 0, 1, 5 }; };
// fromJSON, after `from_json_int(level)`:
if (! (m_level inside { 0, 1, 5 }))
  `uvm_error(get_full_name(), $sformatf("'level' value %0d not in enum", m_level))
```

Fixture: `tests/fixtures/with_plain_enum.json`.

---

## Range and divisibility constraints (numeric)

| Schema                | SV constraint                |
|-----------------------|------------------------------|
| `minimum: N`          | `m_x >= N`                   |
| `maximum: N`          | `m_x <= N`                   |
| `exclusiveMinimum: N` | `m_x > N`                    |
| `exclusiveMaximum: N` | `m_x < N`                    |
| `multipleOf: N`       | `m_x % N == 0`               |

All collected into a single `constraint x_range_c { ...; ...; }`. For arrays
they wrap in a `foreach (m_x[i]) { ... }`.

Fixture: `tests/fixtures/all_types.json` (`i_excl`, `i_mult`).

---

## String length

Runtime length checks after `from_json_string`:

| Schema           | SV check                                                       |
|------------------|----------------------------------------------------------------|
| `minLength: N`   | `if (m_x.len() < N) uvm_error(...)`                            |
| `maxLength: N`   | `if (m_x.len() > N) uvm_error(...)`                            |

These don't take part in randomization; they're validation only.

Fixture: `tests/fixtures/with_validation.json`.

---

## Array constraints

| Schema                  | SV                                                                |
|-------------------------|-------------------------------------------------------------------|
| `minItems: N`           | `constraint x_size_c { m_x.size >= N; ... };`                     |
| `maxItems: N`           | `constraint x_size_c { ... m_x.size <= N; };`                     |
| `uniqueItems: true`     | `constraint x_unique_c { unique { m_x }; };`                      |
| item-level `minimum`/`maximum`/`exclusiveMinimum`/`exclusiveMaximum`/`multipleOf` | wrapped in `foreach (m_x[i]) { m_x[i] ... }` |

`fromJSON` for arrays now resizes `m_x` to the input array's exact length —
larger inputs grow it, smaller inputs shrink it (so old randomized tail
items don't leak through to the dump).

Fixture: `tests/fixtures/all_types.json` (`uniq_arr`, `i_arr`, `i_excl`).

---

## `additionalProperties: false`

Strict objects refuse unknown keys at runtime. The generator emits a
key-iteration loop at the end of `fromJSON` that compares each input key
against the schema's `properties` set.

```json
{ "type": "object",
  "properties": {"a": {"type": "integer"}, "b": {"type": "string"}},
  "additionalProperties": false }
```

```sv
// at the tail of fromJSON:
begin
    ObjectVal_ _obj_jv;
    string _allowed[] = { "a", "b" };
    if ($cast(_obj_jv, jv)) begin
        for (int _i = 0; _i < _obj_jv.size(); _i++) begin
            string _k = _obj_jv.keyAt(_i);
            bit _ok = 0;
            foreach (_allowed[_a]) if (_k == _allowed[_a]) _ok = 1;
            if (!_ok)
                `uvm_error(get_full_name(),
                    $sformatf("unexpected property '%s' (additionalProperties: false)", _k))
        end
    end
end
```

Relies on `ObjectVal_::keyAt(int)` from sv-embed-json. Fixture:
`tests/fixtures/with_strict.json`.

---

## `oneOf` composition

Top-level definitions can use `oneOf` plus a `discriminator` to model a
tagged union. The generator emits a base SV class with a static factory
that switches on the discriminator and constructs the matching subclass;
the branches `extends` the base instead of `uvm_object`.

```json
"AnyMap": {
  "oneOf": [
    {"$ref": "#/definitions/AddrMap"},
    {"$ref": "#/definitions/RegMap"}
  ],
  "discriminator": {"propertyName": "kind"}
}
```

```sv
class AnyMap extends uvm_object;
    static function AnyMap fromJSONFactory(Val_ jv);
        ...
        case (jv.getByKey("kind").asString())
          "addr": begin AddrMap _t = new(""); _t.fromJSON(jv); result = _t; end
          "reg":  begin RegMap _t = new("");  _t.fromJSON(jv); result = _t; end
          default: `uvm_error(...)
        endcase
        return result;
    endfunction
endclass

class AddrMap extends AnyMap; ... endclass
class RegMap  extends AnyMap; ... endclass

// A property typed as the base:
AnyMap m_map;
// in fromJSON:
`from_json_oneof(map, AnyMap)
// in toJSON:
`to_json_oneof(map)   // dispatches polymorphically
```

Each branch must declare a `default` for the discriminator field; that
default is the case label. `oneOf` is **not** supported as an inline
property schema — only at top-level definitions.

`anyOf` is **not** supported.

Fixture: `tests/fixtures/with_oneof.json`.

---

## `$ref`

Intra-document refs (`#/definitions/X`) and cross-file refs are both
supported, resolved by `json_ref_dict.materialize` before parsing. Ref
cycles (recursive types) are **not** supported.

Fixture: `examples/axi4_cfg_schema.json` (Cfg.addr_map → AddrMap).

---

## Recursive `$ref` (self-referential types)

statham raises `FeatureNotImplementedError` on cyclic schemas, so the
generator preprocesses the materialized dict to break self-references.
For each top-level definition, every alias-to-self inside it is replaced
with a stub `{"type": "object", "x-sv-recursive-ref": <name>}`. statham
parses the stub as an empty placeholder class which the SV serializer
filters out of the rendered output; properties that pointed at the stub
get re-typed as the original target class via a side-table.

```json
"definitions": {
  "Tree": {
    "type": "object",
    "properties": {
      "value":    { "type": "integer", "default": 0 },
      "children": { "type": "array",   "items": { "$ref": "#/definitions/Tree" } }
    }
  }
}
```

```sv
class Tree extends uvm_object;
    `uvm_object_utils(Tree)
    rand int  m_value = 0;
    Tree      m_children[];   // not `rand`, no auto-allocate in post_randomize

    virtual function void fromJSON(Val_ jv);
        `from_json_int(value)
        `from_json_object_array(children)   // recurses: each child gets fromJSON
    endfunction
```

Recursive fields are intentionally **not** randomized: an unbounded
`rand` tree would loop in `randomize()`. Populate them explicitly or via
`fromJSON`. v1 supports direct self-recursion (a class referencing itself
through any depth of `properties`/`items`); mutual recursion (`A → B → A`)
is still flagged by statham.

Fixture: `tests/fixtures/with_recursive.json`.

---

## `allOf` (object property merging)

When a top-level definition uses `allOf` to mix in properties from another
object schema, the generator merges the branches' `properties` and
`required` into the parent before parsing. The parent's own definitions
take precedence on conflict; the `allOf` keyword is then stripped so it
doesn't surface as a diagnostic.

```json
"definitions": {
  "Identifiable": {
    "type": "object",
    "properties": {
      "id":   { "type": "integer", "default": 0 },
      "name": { "type": "string",  "default": "" }
    },
    "required": ["id"]
  },
  "Cfg": {
    "type": "object",
    "allOf": [{ "$ref": "#/definitions/Identifiable" }],
    "properties": { "awuser": { "type": "integer" } },
    "required": ["awuser"]
  }
}
```

The merged `Cfg` carries `id`, `name`, `awuser` and `required: [id, awuser]`.
The mixin (`Identifiable`) is also still emitted as a stand-alone class for
direct use.

Branches that aren't object schemas (e.g., composing numeric constraints
on a primitive type) are kept in place and surfaced via `--strict`. `anyOf`
and `not` are not handled.

Fixture: `tests/fixtures/with_allof.json`.

---

## `description` → SV comments

JSON Schema `description` (on a class or a property) is propagated as
`// ...` comments above the corresponding SV declaration. Multi-line
descriptions render as one `//` line each.

```json
{
  "type": "object",
  "description": "Configuration with validation constraints.",
  "properties": {
    "name": { "description": "Display name (3 to 8 chars).", "type": "string" }
  }
}
```

```sv
    // Configuration with validation constraints.
    class Cfg extends uvm_object;
        ...
        // Display name (3 to 8 chars).
        string m_name;
```

Fixture: `tests/fixtures/with_validation.json` (the `Cfg` class and its
`name` property each carry a description).

---

## Diagnostics: `--strict` and per-keyword warnings

The generator walks the resolved schema dict before parsing and emits a
diagnostic for every JSON-Schema assertion keyword it can't model
(`allOf`, `anyOf`, `not`, `if/then/else`, `pattern`, `patternProperties`,
`dependencies` / `dependentRequired` / `dependentSchemas`, `contains` /
`min/maxContains` / `additionalItems`, `min/maxProperties`,
`propertyNames`, `unevaluatedItems` / `unevaluatedProperties`,
`additionalProperties: <schema>`, multi-type `type: [...]`, `type: null`,
unsupported `format` strings on string / integer fields).

```
$ python3 app.py --input my.json --class-out a.sv --tb-out b.sv
warning: definitions/Cfg/properties/name: keyword `pattern` is not
         honored by the SV generator. The schema will validate via
         JSON-Schema tools but the generated SV will not enforce the
         corresponding constraint.
```

Pass `--strict` to turn each warning into an error and abort generation
before any output is written. Tests for every checked-in fixture run a
"zero diagnostics" assertion so a regression here surfaces as a unit
failure, not a runtime surprise.

---

## SV runtime layering

The generated SV depends on three pieces of [sv-embed-json](https://github.com/mpatil/sv-embed-json):

* `json/json_pkg.sv` (the package) — `Val_` value tree, `pJSON` /
  `psJSON` parsers, `mkInt` / `mkReal` / `mkStr` / `mkBool`
  Val_-construction helpers.
* `json/uvm/json_macros.svh` — UVM-aware reader / writer macros over
  `Val_`, with the calling convention
  `\`from_json_<kind>(FIELD, KEY[, EXTRA])` /
  `\`to_json_<kind>(FIELD, KEY[, EXTRA])`. The generator emits exactly
  those calls; the macros handle null-checks, key lookup, type tags,
  and cardinality.
* The non-UVM `Val_` core stays UVM-free; `json_macros.svh` is the
  optional UVM layer.

`sv_tb.f` puts both
`+incdir+sv-embed-json/src/json` and `+incdir+sv-embed-json/src/json/uvm`
on the include path; `serializers/sv_tb_pkg.sv` does
`\`include "json_macros.svh"` so the macros are in scope when
`config_m.sv` is compiled.

---

## Generated UVM artifacts per class

Every generated class:

* `uvm_object_utils(<Name>)` — register the class with UVM's factory.
* `function new(string name = "", uvm_object p__parent = null, <Name> p__root = null)`.
* `function void post_randomize()` — instantiates nested object members so
  randomization recurses correctly.
* `virtual function void fromJSON(Val_ jv)` — populates members from a
  parsed `Val_`. Wrapped in `\`ifdef JSON_PKG`.
* `virtual function ObjectVal_ toJSON()` — emits a fresh `ObjectVal_`.
  Wrapped in `\`ifdef JSON_PKG`.
* `virtual function void do_print(uvm_printer printer)` — UVM-style printing.

All fields are prefixed with `m_`; root pointer is `m__root`; parent
pointer is `m__parent`.
