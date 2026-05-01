# Command

Mutating atoms. WRITE effect. Sub-shape: ScalarCommand. Commands yield nothing.

Core only - shapes and ext/ not included.

## IO

| Name  | Sub-shape     | Signature                               | Effect | Meaning                                  |
| ----- | ------------- | --------------------------------------- | ------ | ---------------------------------------- |
| Print | ScalarCommand | `Print(*values)`                        | WRITE  | print messages to stdout                 |
| Log   | ScalarCommand | `Log(message, *values, level, logger_name)` | WRITE | structured logging at given level    |
| Debug | ScalarCommand | `Debug(*values, labels, prefix)`        | WRITE  | quick debug output for development       |

> `commands/asserts.py` exists but is empty - no asserts shipped yet.
