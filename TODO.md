# Pending JSON Schema features

Drawn from the post-`required-enforcement` feature audit. Loosely ordered by
payoff/effort. "Status" reflects the master / `sv-embed-json-migration`
branch.

| # | Feature                                                     | Effort | Status |
|---|-------------------------------------------------------------|--------|--------|
| 1 | `required` field enforcement (uvm_error on missing key)     | M      | done   |
| 2 | Plain `enum` on string / integer                            | M      | open   |
| 3 | `oneOf` composition (discriminator-based, top-level only)   | L      | done   |
| 4 | `additionalProperties: false` (warn/error on unknown keys)  | S      | open   |
| 5 | `exclusiveMinimum`, `exclusiveMaximum`, `multipleOf`        | XS     | done   |
| 6 | `pattern` (regex) — open / `uniqueItems` — done             | M / S  | partial |
| 7 | Recursive `$ref` (forward declarations + cycle handling)    | M      | open   |
| 8 | `null` type / multi-type unions                             | L      | open   |

## Smaller declarative gaps (would slot into existing serializer pipeline)

* `minLength`, `maxLength` on string fields
* `additionalItems`, `contains`, `minContains`, `maxContains` on arrays
* `propertyNames`, `minProperties`, `maxProperties`, `dependencies`
* `const`
* `if` / `then` / `else` (conditional)
* `description` propagation into generated SV (docstrings or comments)

## Out of scope (for now)

* `format` validators beyond `hex` / `binary` (`date-time`, `uuid`, `email`,
  `ipv4`/`ipv6`, `uri`, `regex`, `json-pointer`)
* `readOnly` / `writeOnly` / `deprecated`
* `contentEncoding` / `contentMediaType` / `contentSchema`
* `$dynamicRef` / `$dynamicAnchor` (2020-12)
