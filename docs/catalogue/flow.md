# Flow

Command-composing atoms. Sub-shapes: Strategy (how children run together) and Control (branching, looping). Flows yield nothing.

Convention: Control names carry the `*Do` suffix to mark them as Flow (effectful) rather than Query (pure). Bare verb forms (`If`, `Switch`, `ForEach`) are reserved for Queries.

Core only - shapes and ext/ not included.

## Strategy

| Name       | Sub-shape | Signature         | Operator | Meaning                              |
| ---------- | --------- | ----------------- | -------- | ------------------------------------ |
| Sequential | Strategy  | `Sequential(*cs)` | `>>`     | run children in order                |
| Parallel   | Strategy  | `Parallel(*cs)`   | `\|`     | run children concurrently            |
| Race       | Strategy  | `Race(*cs)`       | `&`      | first to complete wins               |
| Gather     | Strategy  | `Gather(*cs)`     |          | run concurrently and collect yields  |
| AnyN       | Strategy  | `AnyN(*cs)`       |          | concurrent; succeed if any succeeds  |

## Control

### Branch

| Name     | Sub-shape | Signature                                  | Meaning                              |
| -------- | --------- | ------------------------------------------ | ------------------------------------ |
| IfDo     | Control   | `IfDo(cond, body, else_body=None)`         | run body if cond is truthy           |
| SwitchDo | Control   | `SwitchDo(selector, cases, default=None)`  | multi-way branch on selector value   |

### Loop

| Name      | Sub-shape | Signature                                            | Meaning                                                  |
| --------- | --------- | ---------------------------------------------------- | -------------------------------------------------------- |
| WhileDo   | Control   | `WhileDo(cond, body)`                                | run body while cond holds                                |
| ForeverDo | Control   | `ForeverDo(body)`                                    | run body indefinitely                                    |
| ForEachDo | Control   | `ForEachDo(items, body, item="item")`                | run body per element; binds element to `ctx.attrs[item]` |
| ForRangeDo| Control   | `ForRangeDo(start, stop, body, step=1, index="i")`   | counted loop over `range(start, stop, step)`             |

### Timing

| Name      | Sub-shape | Signature                  | Meaning                                                              |
| --------- | --------- | -------------------------- | -------------------------------------------------------------------- |
| DelayedDo | Control   | `DelayedDo(delay, body)`   | sleep `delay` seconds then run body (sync: time.sleep, async: asyncio.sleep) |
