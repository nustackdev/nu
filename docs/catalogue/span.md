# Span

Transparent Interaction sub-kind. Wraps any Nu (Ref, Query, Command, Flow, or another Span) and yields what its body yields. Sub-shapes: Bracket (boundary semantics) and Policy (per-attempt control).

Core only - shapes and ext/ not included.

## Bracket

-

## Policy

Wraps a body with per-attempt or per-run control - retry, fail-fast, rate limiting.

### Error handling

| Name     | Sub-shape | Signature                                                                                            | Meaning                                              |
| -------- | --------- | ---------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| TryCatch | Policy    | `TryCatch(body, catch=None, finally_=None, errors=Exception)`                                        | try/catch/finally with optional typed exception filter |
| Retry    | Policy    | `Retry(body, max_attempts, delay=0, backoff=1, on_attempt_fail=None, on_success=None, on_fail=None)` | retry on failure with backoff and per-attempt hooks  |

### Time

| Name     | Sub-shape | Signature                                  | Meaning                                              |
| -------- | --------- | ------------------------------------------ | ---------------------------------------------------- |
| Timeout  | Policy    | `Timeout(timeout, body, on_timeout=None)`  | abort if body runs longer than `timeout` seconds     |
| Throttle | Policy    | `Throttle(interval, body)`                 | drop executions within `interval` seconds of prior   |
| Debounce | Policy    | `Debounce(delay, body)`                    | delay execution by `delay`; cancel pending on re-entry |
