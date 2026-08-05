---
title: nu.std.logging
---

Mirrors `logging` 1-1 on the call side. Every call builds a Nu `Log` tree instead of firing immediately; Python's `logging` module is the sink (handlers/formatters/filters stay pure-Python config).

`from nu.std.logging import getLogger, info, warning, error`

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
