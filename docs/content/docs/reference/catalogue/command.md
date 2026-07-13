---
title: Command
---

Mutating atoms. WRITE effect. Sub-shape: ScalarCommand. Commands yield nothing.

Core only - shapes and ext/ not included.

## IO

User-facing commands that write to stdio. All declare `own_effects = {0: WRITE}` on the StdioRef position.

| Name  | Sub-shape     | Signature                                       | Effect | Meaning                              |
| ----- | ------------- | ----------------------------------------------- | ------ | ------------------------------------ |
| Print | ScalarCommand | `Print(*values)`                                | WRITE  | print messages to stdout             |
| Log   | ScalarCommand | `Log(message, *values, level, logger_name)`    | WRITE  | structured logging at given level    |
| Debug | ScalarCommand | `Debug(*values, labels, prefix)`                | WRITE  | quick debug output for development   |

## Stdio low-level

Lower-level stdio Commands operating on a `StdioRef` directly. `Print`, `Log`, `Debug` are sugar over these.

| Name        | Sub-shape     | Signature                | Effect | Meaning                              |
| ----------- | ------------- | ------------------------ | ------ | ------------------------------------ |
| StdioWrite  | ScalarCommand | `StdioWrite(ref, *values)` | WRITE | write values to a stdio stream      |
| StdioFlush  | ScalarCommand | `StdioFlush(ref)`        | WRITE  | flush a stdio stream's buffer        |

> `StdioRead` is a ScalarQuery (lives in queries surface).
> `BufferedStdio` is a Bracket Span (lives in spans surface).
