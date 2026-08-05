---
title: nu.std.decimal
---

Mirrors `decimal` 1-1 for the value type only (module-level contexts/`ROUND_*` are out of scope).

`from nu.std.decimal import Decimal`

| Name    | Sort | Signature         | Effect | Meaning                                                                                          |
| ------- | ---- | ------------------ | ------ | --------------------------------------------------------------------------------------------------- |
| Decimal | Form | `Decimal.of(value)` | pure   | arbitrary-precision decimal, coerced through `str` for exactness; `from_float`, `quantize`/`normalize`/`sqrt`/`exp`/`ln`/`log10`/`compare`/`copy_abs`/`copy_negate`, `adjusted`/`as_integer_ratio`, `is_finite`/`is_infinite`/`is_nan`/`is_zero`/`is_signed`, arithmetic, comparison |
