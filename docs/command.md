# Command

Mutating atoms. WRITE effect. Sub-shape: ScalarCommand. Commands yield nothing.

Partial - samples below to confirm direction.

## IO

| Name  | Sub-shape     | Signature       | Effect | Meaning            |
| ----- | ------------- | --------------- | ------ | ------------------ |
| Print | ScalarCommand | `Print(x)`      | WRITE  | write to stdout    |
| Log   | ScalarCommand | `Log(x, level)` | WRITE  | log at given level |
| Debug | ScalarCommand | `Debug(x)`      | WRITE  | debug-level log    |

> Remaining: asserts.
