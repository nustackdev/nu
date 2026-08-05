---
title: nu.std.datetime
---

Mirrors `datetime` 1-1: five Forms, no module-level functions. Property reads (`.year`, `.hour`, `.days`, ...) reuse core `GetAttr`; arithmetic and comparison reuse the core atoms.

`from nu.std.datetime import date, timedelta`

| Name      | Sort | Signature                                              | Effect | Meaning                                                                                  |
| --------- | ---- | ------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------ |
| timedelta | Form | `timedelta.of(days=, seconds=, ..., weeks=)`            | pure   | a span of time; `.days`/`.seconds`/`.microseconds`, `total_seconds()`, arithmetic, comparison |
| time      | Form | `time.of(hour, minute, second, microsecond)`            | pure   | a wall-clock time of day; `from_iso`, `isoformat()`, `strftime()`, `replace()`, comparison |
| date      | Form | `date.of(year, month, day)`                             | pure   | a calendar date; `today()`, `from_iso`/`from_ordinal`/`from_timestamp`, `weekday()`, `+`/`-` with `timedelta`, comparison |
| datetime  | Form | `datetime.of(year, month, day, hour=, ...)`             | pure   | a date and a time; `now(tz)`, `from_iso`/`from_timestamp`, `combine()`, `date()`/`time()` parts, `+`/`-`, comparison |
| timezone  | Form | `timezone.of(offset, name=None)`                        | pure   | a fixed UTC offset; `utc()`, `utcoffset()`, `tzname()`, `dst()` (always `None`), `eq`/`ne` |
