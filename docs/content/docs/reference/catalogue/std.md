---
title: nu.std
---

Typed Nu surfaces for Python's standard library. Each submodule mirrors a stdlib module by name (`uuid`, `datetime`, `decimal`, ...) - import through the submodule, the way you would the stdlib itself. There is no flat shortcut off `nu.std`.

A value type is a **Form** - the typed access surface you build with `.of(...)` and read/transform with properties and methods (properties reuse core `GetAttr`; arithmetic and comparison reuse the core atoms; only constructors and host-specific methods get new atoms). A module with no central class (`math`, `random`, `time`, `itertools`, ...) is just free functions over Nu terms.

One group per submodule, in source order. Grouped by source file within: `forms.py` (value types), `functions.py` (free functions, constants), `interactions.py` (the atoms - not listed separately here since they mirror the Form methods / functions 1-1; see each module's source for the exact atom name behind a call).

## asyncio

`from nu.std.asyncio import sleep`

No central class - `asyncio` is orchestration (`gather`, `wait`, `create_task`, `run`), and that's already what Nu Flows are. The one leaf primitive Flows can't express is the non-blocking sleep.

| Name  | Sort        | Signature      | Effect              | Meaning                                             |
| ----- | ----------- | -------------- | -------------------- | --------------------------------------------------- |
| sleep | ScalarQuery | `sleep(delay)` | non-det, async-only | suspend the coroutine without blocking the loop (mirrors `asyncio.sleep`); sync sibling is `nu.std.time.sleep` |

## cmath

`from nu.std.cmath import complex, sqrt, phase, pi`

Hybrid surface: `complex` is a builtin with no module of its own, `cmath` is its companion function set, so the two co-locate here.

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

## datetime

`from nu.std.datetime import date, timedelta`

Mirrors `datetime` 1-1: five Forms, no module-level functions. Property reads (`.year`, `.hour`, `.days`, ...) reuse core `GetAttr`; arithmetic and comparison reuse the core atoms.

| Name      | Sort | Signature                                              | Effect | Meaning                                                                                  |
| --------- | ---- | ------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------ |
| timedelta | Form | `timedelta.of(days=, seconds=, ..., weeks=)`            | pure   | a span of time; `.days`/`.seconds`/`.microseconds`, `total_seconds()`, arithmetic, comparison |
| time      | Form | `time.of(hour, minute, second, microsecond)`            | pure   | a wall-clock time of day; `from_iso`, `isoformat()`, `strftime()`, `replace()`, comparison |
| date      | Form | `date.of(year, month, day)`                             | pure   | a calendar date; `today()`, `from_iso`/`from_ordinal`/`from_timestamp`, `weekday()`, `+`/`-` with `timedelta`, comparison |
| datetime  | Form | `datetime.of(year, month, day, hour=, ...)`             | pure   | a date and a time; `now(tz)`, `from_iso`/`from_timestamp`, `combine()`, `date()`/`time()` parts, `+`/`-`, comparison |
| timezone  | Form | `timezone.of(offset, name=None)`                        | pure   | a fixed UTC offset; `utc()`, `utcoffset()`, `tzname()`, `dst()` (always `None`), `eq`/`ne` |

## decimal

`from nu.std.decimal import Decimal`

Mirrors `decimal` 1-1 for the value type only (module-level contexts/`ROUND_*` are out of scope).

| Name    | Sort | Signature         | Effect | Meaning                                                                                          |
| ------- | ---- | ------------------ | ------ | --------------------------------------------------------------------------------------------------- |
| Decimal | Form | `Decimal.of(value)` | pure   | arbitrary-precision decimal, coerced through `str` for exactness; `from_float`, `quantize`/`normalize`/`sqrt`/`exp`/`ln`/`log10`/`compare`/`copy_abs`/`copy_negate`, `adjusted`/`as_integer_ratio`, `is_finite`/`is_infinite`/`is_nan`/`is_zero`/`is_signed`, arithmetic, comparison |

## fin

`from nu.std.fin import Percentage, BasisPoint`

Not a stdlib module - Nu's own financial value types, built the same way (a native frozen dataclass wrapped by a Form).

| Name        | Sort | Signature               | Effect | Meaning                                                                                          |
| ----------- | ---- | ------------------------ | ------ | --------------------------------------------------------------------------------------------------- |
| Percentage  | Form | `Percentage.of(value)`  | pure   | a percentage (`75.5` = 75.5%); `from_dec`/`from_bps`/`from_ratio`, `to_dec`/`to_bps`/`to_float`, `apply`/`add_to`/`sub_from`, `is_valid`/`clamp`, arithmetic, comparison |
| BasisPoint  | Form | `BasisPoint.of(value)`  | pure   | a basis-point count (`500` = 5%), stored as int for exact rate math; `from_pct`/`from_dec`, `to_pct`/`to_dec`/`to_int`, `apply`/`add_to`/`sub_from`, arithmetic, comparison |

Raw native values (no Nu wrapping) are importable alongside the Forms: `PyPercentage`, `PyBasisPoint` (frozen dataclasses in `nu.std.fin.native`).

## fractions

`from nu.std.fractions import Fraction`

Mirrors `fractions` 1-1: one Form, no module-level functions.

| Name     | Sort | Signature                       | Effect | Meaning                                                                                    |
| -------- | ---- | -------------------------------- | ------ | --------------------------------------------------------------------------------------------- |
| Fraction | Form | `Fraction.of(numerator, denominator=1)` | pure | exact rational number; `from_float`/`from_decimal`/`from_str`, `.numerator`/`.denominator`, `limit_denominator()`, `as_integer_ratio()`, arithmetic, comparison |

## functools

`from nu.std.functools import reduce`

Only `reduce` is modeled - the one member that is a runtime value fold. `partial`/`cache`/decorators are out of the value model (no first-class function value, no effect model yet).

| Name   | Sort      | Signature                                | Effect | Meaning                                                                 |
| ------ | --------- | ------------------------------------------ | ------ | -------------------------------------------------------------------------- |
| reduce | Reduction | `reduce(function, iterable, initializer=)` | pure   | left-to-right fold; `function` reads the accumulator/item via typed `AttrRef`s (mirrors `functools.reduce`) |

## itertools

`from nu.std.itertools import chain, islice, count`

Gap-fill over Nu core: members core already covers (`map`/`filter`/`zip`/`sorted`/`enumerate`/`reversed`/sums) are not repeated. Every member is a hand-written `StreamQuery` atom except `tee`.

### Infinite sources

| Name   | Sort        | Signature             | Effect | Meaning                                    |
| ------ | ----------- | ----------------------- | ------ | -------------------------------------------- |
| count  | StreamQuery | `count(start=0, step=1)` | pure | unbounded arithmetic stream; bound with `islice` |
| cycle  | StreamQuery | `cycle(iterable)`       | pure   | repeat a source forever                     |
| repeat | StreamQuery | `repeat(elem, times=None)` | pure | yield `elem` `times` times, or forever    |

### Pure combinators

| Name                          | Sort        | Signature                                        | Effect | Meaning                                     |
| ----------------------------- | ----------- | -------------------------------------------------- | ------ | ---------------------------------------------- |
| chain                         | StreamQuery | `chain(*iterables)`                                | pure   | concatenate sources end to end                 |
| chain_from_iterable           | StreamQuery | `chain_from_iterable(iterable)`                    | pure   | flatten an iterable of iterables one level     |
| islice                        | StreamQuery | `islice(iterable, *args)`                          | pure   | lazy slice (`stop` \| `start,stop` \| `start,stop,step`) |
| compress                      | StreamQuery | `compress(data, selectors)`                        | pure   | keep `data` where `selectors` is truthy        |
| pairwise                      | StreamQuery | `pairwise(iterable)`                               | pure   | overlapping consecutive pairs                  |
| batched                       | StreamQuery | `batched(iterable, n)`                             | pure   | tuples of up to `n` items                      |
| zip_longest                   | StreamQuery | `zip_longest(*iterables, fillvalue=None)`          | pure   | zip to the longest, padding short sources      |
| product                       | StreamQuery | `product(*iterables, repeat=1)`                    | pure   | cartesian product                              |
| permutations                  | StreamQuery | `permutations(iterable, r=None)`                   | pure   | `r`-length ordered arrangements                |
| combinations                  | StreamQuery | `combinations(iterable, r)`                        | pure   | `r`-length sorted subsequences                 |
| combinations_with_replacement | StreamQuery | `combinations_with_replacement(iterable, r)`       | pure   | `r`-length subsequences allowing repeats       |

### Higher-order

| Name       | Sort        | Signature                          | Effect | Meaning                                                        |
| ---------- | ----------- | ------------------------------------ | ------ | ------------------------------------------------------------------ |
| takewhile  | StreamQuery | `takewhile(predicate, iterable)`     | pure   | yield while `predicate` holds, stop at the first falsy             |
| dropwhile  | StreamQuery | `dropwhile(predicate, iterable)`     | pure   | skip while `predicate` holds, then yield the rest                  |
| filterfalse| StreamQuery | `filterfalse(predicate, iterable)`   | pure   | keep items where `predicate` is falsy                              |
| accumulate | StreamQuery | `accumulate(iterable, func=None)`    | pure   | running accumulation (sum by default, or a Nu term over acc/item)   |
| starmap    | StreamQuery | `starmap(function, iterable)`       | pure   | apply `function` to unpacked tuple items                           |
| groupby    | StreamQuery | `groupby(iterable, key=None)`        | pure   | group consecutive items by key -> `(key, tuple(group))` pairs      |

### tee

| Name | Sort        | Signature          | Effect | Meaning                                                     |
| ---- | ----------- | -------------------- | ------ | ---------------------------------------------------------------- |
| tee  | ScalarQuery | `tee(iterable, n=2)` | pure   | split into `n` independent iterators -> `Any` holding a tuple (not a stream) |

## logging

`from nu.std.logging import getLogger, info, warning, error`

Mirrors `logging` 1-1 on the call side. Every call builds a Nu `Log` tree instead of firing immediately; Python's `logging` module is the sink (handlers/formatters/filters stay pure-Python config).

| Name      | Sort          | Signature                                        | Effect | Meaning                                                     |
| --------- | ------------- | --------------------------------------------------- | ------ | ---------------------------------------------------------------- |
| Logger    | -             | `Logger(name)`                                      | -      | bound-logger class returned by `getLogger`; call-surface only, not a `logging.Logger` |
| getLogger | -             | `getLogger(name=None)`                              | pure   | return a bound `Logger` (root logger if `name` omitted)           |
| log       | ScalarCommand | `log(level, msg, *args, extra=None)`               | WRITE  | root-logger record at `level` (mirrors `logging.log`); `Logger.log` is the bound-instance sibling |
| debug     | ScalarCommand | `debug(msg, *args, extra=None)`                    | WRITE  | root-logger DEBUG record                                          |
| info      | ScalarCommand | `info(msg, *args, extra=None)`                     | WRITE  | root-logger INFO record                                           |
| warning   | ScalarCommand | `warning(msg, *args, extra=None)`                  | WRITE  | root-logger WARNING record                                        |
| warn      | ScalarCommand | `warn(msg, *args, extra=None)`                     | WRITE  | alias of `warning` (stdlib-deprecated, kept for parity)            |
| error     | ScalarCommand | `error(msg, *args, extra=None)`                    | WRITE  | root-logger ERROR record                                          |
| critical  | ScalarCommand | `critical(msg, *args, extra=None)`                 | WRITE  | root-logger CRITICAL record                                       |

Level constants (mirror `logging.*` for import parity, plain ints): `DEBUG`, `INFO`, `WARNING`, `WARN`, `ERROR`, `CRITICAL`, `FATAL`, `NOTSET`.

## math

`from nu.std.math import sqrt, pi`

No central class - free functions and constants mirroring `math` 1-1.

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

## pathlib

`from nu.std.pathlib import Path`

Mirrors `pathlib` 1-1, backed by `PurePath` - only lexical path operations, no filesystem I/O (deferred: `exists`, `read_text`, `iterdir`, `glob`, ...).

| Name | Sort | Signature       | Effect | Meaning                                                                                             |
| ---- | ---- | ---------------- | ------ | ------------------------------------------------------------------------------------------------------ |
| Path | Form | `Path.of(*segments)` | pure | pure path; `cwd()`/`home()`, `.name`/`.stem`/`.suffix`/`.parts`/`.parent`/`.root`/`.anchor`/`.drive`, `with_name`/`with_stem`/`with_suffix`/`joinpath`/`relative_to`, `/` operator, `as_posix()`/`as_uri()`, `match()`/`is_absolute()`/`is_relative_to()`, comparison |

## random

`from nu.std.random import randint, choice`

No central class - free functions over the global RNG. Every function is non-deterministic (reads the RNG) so its atom is never constant-folded. Deferred until the effect model lands: `seed`, `shuffle`, `getstate`/`setstate`.

| Name          | Sort        | Signature               | Effect  | Meaning                                             |
| ------------- | ----------- | -------------------------- | ------- | ------------------------------------------------------ |
| random        | ScalarQuery | `random()`                 | non-det | float in `[0.0, 1.0)`                                   |
| uniform       | ScalarQuery | `uniform(a, b)`             | non-det | float in `[a, b]`                                       |
| randint       | ScalarQuery | `randint(a, b)`             | non-det | int `N` with `a <= N <= b`                              |
| randrange     | ScalarQuery | `randrange(start, stop)`    | non-det | int in `range(start, stop)`                             |
| getrandbits   | ScalarQuery | `getrandbits(k)`            | non-det | non-negative int with `k` random bits                  |
| choice        | ScalarQuery | `choice(seq)`               | non-det | one random element of `seq` -> `Any`                    |
| choices       | ScalarQuery | `choices(population, k)`    | non-det | `k`-sized list drawn with replacement -> `List`         |
| sample        | ScalarQuery | `sample(population, k)`     | non-det | `k`-sized list drawn without replacement -> `List`      |
| gauss         | ScalarQuery | `gauss(mu, sigma)`          | non-det | Gaussian draw                                            |
| normalvariate | ScalarQuery | `normalvariate(mu, sigma)`  | non-det | normal draw                                              |
| expovariate   | ScalarQuery | `expovariate(lambd)`        | non-det | exponential draw with rate `lambd`                      |
| triangular    | ScalarQuery | `triangular(low, high)`     | non-det | triangular draw between `low` and `high`                |

## time

`from nu.std.time import monotonic, sleep`

No central class - free functions over the process clock. Every clock read is non-deterministic. Async sibling of `sleep` lives in `nu.std.asyncio`.

| Name             | Sort        | Signature          | Effect              | Meaning                                  |
| ---------------- | ----------- | -------------------- | -------------------- | -------------------------------------------- |
| time             | ScalarQuery | `time()`            | non-det              | seconds since the epoch -> `Float`             |
| monotonic        | ScalarQuery | `monotonic()`       | non-det              | monotonic clock, seconds -> `Float`            |
| perf_counter     | ScalarQuery | `perf_counter()`    | non-det              | highest-resolution timer, seconds -> `Float`   |
| process_time     | ScalarQuery | `process_time()`    | non-det              | process CPU time, seconds -> `Float`           |
| time_ns          | ScalarQuery | `time_ns()`         | non-det              | seconds since the epoch, nanoseconds -> `Int`  |
| monotonic_ns     | ScalarQuery | `monotonic_ns()`    | non-det              | monotonic clock, nanoseconds -> `Int`          |
| perf_counter_ns  | ScalarQuery | `perf_counter_ns()` | non-det              | highest-resolution timer, nanoseconds -> `Int` |
| sleep            | ScalarQuery | `sleep(secs)`       | non-det, sync-only   | block for `secs` seconds, yields `None`        |

## uuid

`from nu.std.uuid import UUID, uuid4`

Mirrors `uuid` 1-1: `UUID` is the class (a Form); `uuid1`/`uuid3`/`uuid4`/`uuid5` are the module-level generator functions.

### Value type

| Name | Sort | Signature   | Effect | Meaning                                                                                    |
| ---- | ---- | ------------ | ------ | ---------------------------------------------------------------------------------------------- |
| UUID | Form | `UUID.of(...)` (via `from_str`/`from_bytes`/`from_int`) | pure | UUID; `.version`/`.variant`/`.time`/`.clock_seq`/`.node`, `.hex`/`.urn`/`.bytes`/`.bytes_le`/`.int_`, comparison |

### Functions

| Name  | Sort        | Signature                          | Effect  | Meaning                                       |
| ----- | ----------- | ------------------------------------ | ------- | ------------------------------------------------ |
| uuid4 | ScalarQuery | `uuid4()`                            | non-det | random UUID (version 4)                          |
| uuid1 | ScalarQuery | `uuid1(node=None, clock_seq=None)`   | non-det | host/time UUID (version 1)                       |
| uuid3 | ScalarQuery | `uuid3(namespace, name)`             | pure    | name-based MD5 UUID (version 3)                  |
| uuid5 | ScalarQuery | `uuid5(namespace, name)`             | pure    | name-based SHA-1 UUID (version 5)                |
