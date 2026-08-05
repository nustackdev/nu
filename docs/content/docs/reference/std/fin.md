---
title: nu.std.fin
---

Not a stdlib module - Nu's own financial value types, built the same way (a native frozen dataclass wrapped by a Form).

`from nu.std.fin import Percentage, BasisPoint`

| Name        | Sort | Signature               | Effect | Meaning                                                                                          |
| ----------- | ---- | ------------------------ | ------ | --------------------------------------------------------------------------------------------------- |
| Percentage  | Form | `Percentage.of(value)`  | pure   | a percentage (`75.5` = 75.5%); `from_dec`/`from_bps`/`from_ratio`, `to_dec`/`to_bps`/`to_float`, `apply`/`add_to`/`sub_from`, `is_valid`/`clamp`, arithmetic, comparison |
| BasisPoint  | Form | `BasisPoint.of(value)`  | pure   | a basis-point count (`500` = 5%), stored as int for exact rate math; `from_pct`/`from_dec`, `to_pct`/`to_dec`/`to_int`, `apply`/`add_to`/`sub_from`, arithmetic, comparison |

Raw native values (no Nu wrapping) are importable alongside the Forms: `PyPercentage`, `PyBasisPoint` (frozen dataclasses in `nu.std.fin.native`).
