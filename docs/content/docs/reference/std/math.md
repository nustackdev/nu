---
title: nu.std.math
---

No central class - free functions and constants mirroring `math` 1-1.

`from nu.std.math import sqrt, pi`

### Functions

| Name      | Sort        | Signature              | Effect | Meaning                                     |
| --------- | ----------- | ------------------------ | ------ | ---------------------------------------------- |
| sqrt      | ScalarQuery | `sqrt(x)`               | pure   | square root -> `Float`                         |
| pow       | ScalarQuery | `pow(base, exp)`        | pure   | `base ** exp` -> `Float`                       |
| exp       | ScalarQuery | `exp(x)`                | pure   | `e ** x` -> `Float`                             |
| isqrt     | ScalarQuery | `isqrt(x)`              | pure   | integer square root -> `Int`                   |
| hypot     | ScalarQuery | `hypot(x, y)`           | pure   | Euclidean norm -> `Float`                      |
| log       | ScalarQuery | `log(x, base=None)`     | pure   | natural log, or log to `base` -> `Float`       |
| log2      | ScalarQuery | `log2(x)`               | pure   | base-2 log -> `Float`                           |
| log10     | ScalarQuery | `log10(x)`              | pure   | base-10 log -> `Float`                          |
| sin       | ScalarQuery | `sin(x)`                | pure   | sine of `x` radians -> `Float`                  |
| cos       | ScalarQuery | `cos(x)`                | pure   | cosine of `x` radians -> `Float`                |
| tan       | ScalarQuery | `tan(x)`                | pure   | tangent of `x` radians -> `Float`               |
| asin      | ScalarQuery | `asin(x)`               | pure   | arc sine in radians -> `Float`                  |
| acos      | ScalarQuery | `acos(x)`               | pure   | arc cosine in radians -> `Float`                |
| atan      | ScalarQuery | `atan(x)`               | pure   | arc tangent in radians -> `Float`               |
| atan2     | ScalarQuery | `atan2(y, x)`           | pure   | quadrant-aware arc tangent of `y/x` -> `Float`  |
| degrees   | ScalarQuery | `degrees(x)`            | pure   | radians to degrees -> `Float`                   |
| radians   | ScalarQuery | `radians(x)`            | pure   | degrees to radians -> `Float`                   |
| floor     | ScalarQuery | `floor(x)`              | pure   | floor -> `Int`                                  |
| ceil      | ScalarQuery | `ceil(x)`               | pure   | ceiling -> `Int`                                |
| trunc     | ScalarQuery | `trunc(x)`              | pure   | truncate toward zero -> `Int`                   |
| fabs      | ScalarQuery | `fabs(x)`               | pure   | absolute value -> `Float`                       |
| copysign  | ScalarQuery | `copysign(x, y)`        | pure   | `x` with the sign of `y` -> `Float`             |
| fmod      | ScalarQuery | `fmod(x, y)`            | pure   | C-library `fmod` -> `Float`                     |
| gcd       | ScalarQuery | `gcd(a, b)`             | pure   | greatest common divisor -> `Int`                |
| factorial | ScalarQuery | `factorial(x)`          | pure   | `x!` -> `Int`                                   |
| isclose   | ScalarQuery | `isclose(a, b)`         | pure   | approximately equal -> `Bool`                   |
| isnan     | ScalarQuery | `isnan(x)`              | pure   | is NaN -> `Bool`                                |
| isinf     | ScalarQuery | `isinf(x)`              | pure   | is +/- infinity -> `Bool`                       |
| isfinite  | ScalarQuery | `isfinite(x)`           | pure   | is finite -> `Bool`                             |

### Constants

| Name | Sort    | Signature | Effect | Meaning            |
| ---- | ------- | --------- | ------ | -------------------- |
| pi   | Literal | `pi`      | pure   | float pi              |
| e    | Literal | `e`       | pure   | float e               |
| tau  | Literal | `tau`     | pure   | float tau (`2*pi`)    |
| inf  | Literal | `inf`     | pure   | float infinity        |
| nan  | Literal | `nan`     | pure   | float NaN             |
