---
title: nu.std.time
---

No central class - free functions over the process clock. Every clock read is non-deterministic. Async sibling of `sleep` lives in `nu.std.asyncio`.

`from nu.std.time import monotonic, sleep`

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
