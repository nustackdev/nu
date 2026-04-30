# Flow

Command-composing atoms. Sub-shapes: Strategy, Control. Flows yield nothing.

Partial - samples below to confirm direction.

## Strategy

| Name       | Sub-shape | Signature         | Operator | Meaning                         |
| ---------- | --------- | ----------------- | -------- | ------------------------------- |
| Sequential | Strategy  | `Sequential(*cs)` | `>>`     | run children in order           |
| Parallel   | Strategy  | `Parallel(*cs)`   | `\|`     | run children concurrently       |
| Race       | Strategy  | `Race(*cs)`       | `&`      | first to finish wins            |
| Gather     | Strategy  | `Gather(*cs)`     |          | parallel + collect all results  |
| ParAny     | Strategy  | `ParAny(*cs)`     |          | parallel + first non-EMPTY wins |

## Control

| Name      | Sub-shape | Signature                     | Meaning                  |
| --------- | --------- | ----------------------------- | ------------------------ |
| IfDo      | Control   | `IfDo(cond, then, else_)`     | conditional Command      |
| SwitchDo  | Control   | `SwitchDo(...)`               | multi-branch Command     |
| ForEachDo | Control   | `ForEachDo(stream, body)`     | run body per element     |
| WhileDo   | Control   | `WhileDo(cond, body)`         | run body while cond holds|
| DoWhile   | Control   | `DoWhile(body, cond)`         | run body, then while cond|
| Forever   | Control   | `Forever(body)`               | unbounded loop           |
| ForRange  | Control   | `ForRange(start, stop, body)` | loop over integer range  |
