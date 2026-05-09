# JSON Schema features

Snapshot of every JSON Schema construct this generator either supports or
has explicitly punted on. Mirrors `docs/FEATURES.md` (which has full schema
→ SV examples for everything that's already done).

For features that already work, see [`docs/FEATURES.md`](docs/FEATURES.md).
This file is the to-do list for what's still open.

## Done

* Primitive types: `string`, `integer`, `number`, `boolean`, `object`, `array`
* `default`
* `required`
* `const` (string / integer / boolean)
* `description` (propagated to SV `//` comments)
* Bit vectors: `format: "hex"`, `format: "binary"`, vendor `x-sv-width`
* Integer `format: "int32"` / `"int64"` (→ SV `int` / `longint`)
* Enums: object-with-enum (statham idiom), plain `enum` on string, plain
  `enum` on integer
* Numeric: `minimum`, `maximum`, `exclusiveMinimum`, `exclusiveMaximum`,
  `multipleOf`
* String length: `minLength`, `maxLength`
* Array: `minItems`, `maxItems`, `uniqueItems`, item-level numeric
  constraints
* Object strictness: `additionalProperties: false`
* `oneOf` composition with `discriminator` (top-level definitions only)
* `$ref` (intra-document and external file)
* Diagnostics for unsupported standard keywords (`--strict` to fail
  codegen on any drop).

## Open

Loosely ordered by payoff / effort. Run with `--strict` to turn any
silently-dropped open item into a hard error at codegen time.

| Feature                                                                       | Effort | Notes |
|-------------------------------------------------------------------------------|--------|-------|
| `allOf` (composition / property merging)                                      | M      | Most common composition pattern after `oneOf`. |
| Recursive `$ref` (forward declarations + cycle handling)                      | M      | Needed for tree-shaped configs. |
| `minProperties` / `maxProperties` (object size guards)                        | S      | Same fromJSON-guard pattern as `additionalProperties: false`. |
| `pattern` (regex on strings)                                                  | M      | SV has no clean regex story — runtime validation only. Low payoff. |
| `null` type / multi-type unions (`["string", "null"]`)                        | L      | Today approximated by `required: false`. |
| `additionalItems`, `contains`, `minContains`, `maxContains`                   | S      | Niche. |
| `propertyNames`, `dependencies` / `dependentRequired` / `dependentSchemas`    | S each | Niche. |
| `not` (negative composition)                                                  | M      | Lower payoff than `allOf`. |
| `anyOf` (broader composition)                                                 | L      | We already have `oneOf` with discriminator. |
| `if` / `then` / `else` (conditional schemas)                                  | L      | Big design choice for SV mapping. |
| `unevaluatedItems` / `unevaluatedProperties`                                  | M      | 2019-09+ keyword. |

## Out of scope (for now)

* `format` validators beyond `hex` / `binary` (`date-time`, `uuid`, `email`,
  `ipv4`/`ipv6`, `uri`, `regex`, `json-pointer`) — no obvious SV mapping.
* `readOnly` / `writeOnly` / `deprecated` — annotation-only; no runtime
  effect.
* `contentEncoding` / `contentMediaType` / `contentSchema` — outside the
  hardware-config use case.
* `$dynamicRef` / `$dynamicAnchor` (2020-12) — not modeled by upstream
  statham.
* `anyOf`, `not` — design choice (we picked `oneOf` only); revisit if a
  concrete need shows up.
