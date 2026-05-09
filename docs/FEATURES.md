# Supported features

One section per JSON Schema construct that the generator handles, with the
input shape, the generated SystemVerilog, and a pointer to the fixture in
`tests/fixtures/` that exercises it. The construct **not** listed here is, by
construction, not implemented; see `TODO.md` for the status of every gap.

The "fixture" pointer lets the docs and the tests stay in lockstep — every
section maps to a checked-in schema + golden output + e2e test.

---

## Primitive types

| JSON type   | SV mapping                       | Notes                  |
|-------------|----------------------------------|------------------------|
| `string`    | `string m_x;`                    | Not `rand` by default. |
| `integer`   | `rand int m_x;`                  |                        |
| `number`    | `real m_x;`                      |                        |
| `boolean`   | `rand bit m_x;`                  | 0/1.                   |
| `object`    | nested generated class           |                        |
| `array`     | dynamic array `m_x[]` of inner   |                        |

`null` and multi-type unions (`["string", "null"]`) are **not** supported.

Fixture: `tests/fixtures/all_types.json`.

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
