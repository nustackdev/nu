---
title: nu.std.functools
---

Only `reduce` is modeled - the one member that is a runtime value fold. `partial`/`cache`/decorators are out of the value model (no first-class function value, no effect model yet).

`from nu.std.functools import reduce`

| Name   | Sort      | Signature                                | Effect | Meaning                                                                 |
| ------ | --------- | ------------------------------------------ | ------ | -------------------------------------------------------------------------- |
| reduce | Reduction | `reduce(function, iterable, initializer=)` | pure   | left-to-right fold; `function` reads the accumulator/item via typed `AttrRef`s (mirrors `functools.reduce`) |
