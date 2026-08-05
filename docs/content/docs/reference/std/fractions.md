---
title: nu.std.fractions
---

Mirrors `fractions` 1-1: one Form, no module-level functions.

`from nu.std.fractions import Fraction`

| Name     | Sort | Signature                       | Effect | Meaning                                                                                    |
| -------- | ---- | -------------------------------- | ------ | --------------------------------------------------------------------------------------------- |
| Fraction | Form | `Fraction.of(numerator, denominator=1)` | pure | exact rational number; `from_float`/`from_decimal`/`from_str`, `.numerator`/`.denominator`, `limit_denominator()`, `as_integer_ratio()`, arithmetic, comparison |
