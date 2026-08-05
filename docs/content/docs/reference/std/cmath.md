---
title: nu.std.cmath
---

Hybrid surface: `complex` is a builtin with no module of its own, `cmath` is its companion function set, so the two co-locate here.

`from nu.std.cmath import complex, sqrt, phase, pi`

### Value type

| Name    | Sort | Signature                | Effect | Meaning                                                                 |
| ------- | ---- | ------------------------ | ------ | ------------------------------------------------------------------------ |
| complex | Form | `complex.of(real, imag)` | pure   | complex number; `.real`/`.imag`, `conjugate()`, arithmetic, `eq`/`ne` (not orderable) |

### Functions

| Name     | Sort        | Signature               | Effect | Meaning                                  |
| -------- | ----------- | ----------------------- | ------ | ----------------------------------------- |
| sqrt     | ScalarQuery | `sqrt(x)`               | pure   | square root                               |
| exp      | ScalarQuery | `exp(x)`                | pure   | `e ** x`                                  |
| log      | ScalarQuery | `log(x, base=None)`     | pure   | natural log, or log to `base`             |
| log10    | ScalarQuery | `log10(x)`              | pure   | base-10 log                               |
| sin      | ScalarQuery | `sin(x)`                | pure   | sine                                      |
| cos      | ScalarQuery | `cos(x)`                | pure   | cosine                                    |
| tan      | ScalarQuery | `tan(x)`                | pure   | tangent                                   |
| asin     | ScalarQuery | `asin(x)`               | pure   | arc sine                                  |
| acos     | ScalarQuery | `acos(x)`               | pure   | arc cosine                                |
| atan     | ScalarQuery | `atan(x)`               | pure   | arc tangent                               |
| sinh     | ScalarQuery | `sinh(x)`               | pure   | hyperbolic sine                           |
| cosh     | ScalarQuery | `cosh(x)`               | pure   | hyperbolic cosine                         |
| tanh     | ScalarQuery | `tanh(x)`               | pure   | hyperbolic tangent                        |
| phase    | ScalarQuery | `phase(x)`              | pure   | phase angle in radians -> `Float`         |
| polar    | ScalarQuery | `polar(x)`              | pure   | `(r, phi)` pair -> `Tuple`                |
| rect     | ScalarQuery | `rect(r, phi)`          | pure   | complex from modulus + phase              |
| isnan    | ScalarQuery | `isnan(x)`              | pure   | has a NaN component -> `Bool`             |
| isinf    | ScalarQuery | `isinf(x)`              | pure   | has an infinite component -> `Bool`       |
| isfinite | ScalarQuery | `isfinite(x)`           | pure   | both components finite -> `Bool`          |
| isclose  | ScalarQuery | `isclose(a, b)`         | pure   | approximately equal -> `Bool`             |

### Constants

| Name | Sort    | Signature | Effect | Meaning                     |
| ---- | ------- | --------- | ------ | --------------------------- |
| pi   | Literal | `pi`      | pure   | float pi                    |
| e    | Literal | `e`       | pure   | float e                     |
| tau  | Literal | `tau`     | pure   | float tau (`2*pi`)          |
| inf  | Literal | `inf`     | pure   | float infinity              |
| nan  | Literal | `nan`     | pure   | float NaN                   |
| infj | Literal | `infj`    | pure   | complex infinity            |
| nanj | Literal | `nanj`    | pure   | complex NaN                 |
