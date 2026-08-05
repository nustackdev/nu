---
title: Std
---

Typed Nu surfaces for Python's standard library. Each submodule mirrors a stdlib module by name; import through the submodule the way you would the stdlib itself. There is no flat shortcut off `nu.std`.

A value type is a **Form**: the typed access surface you build with `.of(...)` and read/transform with properties and methods. Property reads reuse core `GetAttr`; arithmetic and comparison reuse the core atoms; only constructors and host-specific methods get new atoms. A module with no central class (`math`, `random`, `time`, `itertools`, ...) is just free functions over Nu terms.

| Module | Import | What |
| --- | --- | --- |
| [asyncio](asyncio.md) | `nu.std.asyncio` | Non-blocking sleep. Orchestration is Flows. |
| [cmath](cmath.md) | `nu.std.cmath` | Complex numbers + companion functions. |
| [datetime](datetime.md) | `nu.std.datetime` | date, time, datetime, timedelta, timezone. |
| [decimal](decimal.md) | `nu.std.decimal` | Arbitrary-precision Decimal. |
| [fin](fin.md) | `nu.std.fin` | Nu's own Percentage, BasisPoint. |
| [fractions](fractions.md) | `nu.std.fractions` | Exact rational Fraction. |
| [functools](functools.md) | `nu.std.functools` | reduce. |
| [itertools](itertools.md) | `nu.std.itertools` | Gap-fill combinators over Nu core. |
| [logging](logging.md) | `nu.std.logging` | Bound loggers and record commands. |
| [math](math.md) | `nu.std.math` | Real math functions and constants. |
| [pathlib](pathlib.md) | `nu.std.pathlib` | Lexical PurePath, no filesystem I/O. |
| [random](random.md) | `nu.std.random` | Non-deterministic draws. |
| [time](time.md) | `nu.std.time` | Wall-clock and monotonic timers, blocking sleep. |
| [uuid](uuid.md) | `nu.std.uuid` | UUID Form and generators. |
