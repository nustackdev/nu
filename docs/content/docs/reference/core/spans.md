---
title: nu.spans
---

Transparent wrappers around a body: forward the body's yield unchanged
(scalar, stream, or nothing) and shape the surroundings - execution policy on
failure or in time (Policy), or a lifecycle boundary opened before and torn
down after (Bracket). Flat-exported at `nu.*`.

`from nu import TryCatch, Retry, Timeout, Throttle, Debounce, Snapshot, Transaction`

## Policy

Execution policy around a body: re-run on failure, bound by wall clock,
rate-limit. `errors` (pure-Python, not a Nu child) scopes retry/catch to a
typed exception; outside it, the exception propagates unretried.

| Name     | Sort          | Signature                                                                                          | Effect              | Meaning                                                              |
| -------- | ------------- | --------------------------------------------------------------------------------------------------- | -------------------- | --------------------------------------------------------------------- |
| TryCatch | Span(Policy)  | `TryCatch(body, catch=None, finally_=None, errors=None, error_key="error")`                          | forwards body        | try/catch/finally with a typed error filter; error lands in `ctx.attrs` |
| Retry    | Span(Policy)  | `Retry(body, *, max_attempts=3, delay=0.0, backoff=1.0, jitter=0.0, errors=None, on_attempt_fail=None, on_success=None, on_fail=None, error_key="error", attempt_key="attempt")` | forwards body | re-run body on matching failure; full backoff/jitter/hooks on async path only |
| Timeout  | Span(Policy)  | `Timeout(timeout, body, on_timeout=None)`                                                            | forwards body, async-only | bound body by a wall-clock limit; `on_timeout` runs (or raises) on expiry |
| Throttle | Span(Policy)  | `Throttle(interval, body)`                                                                           | forwards body, async-only | drop body runs inside `interval` of the prior run; yields `None` when dropped |
| Debounce | Span(Policy)  | `Debounce(delay, body)`                                                                              | forwards body (delayed), async-only | cancel a pending run on re-entry; only the last call in a burst fires, detached |

## Bracket

Lifecycle boundary around a body: open a scope before, commit or roll back
after. The core ships both as pass-throughs (a bare bracket just runs its
body); a fabric subclasses them to drive a real store.

| Name        | Sort          | Signature                    | Effect       | Meaning                                                     |
| ----------- | ------------- | ----------------------------- | ------------ | ------------------------------------------------------------ |
| Snapshot    | Span(Bracket) | `Snapshot(body)`               | forwards body | read-only boundary: snapshot the body's reads, no commit on success |
| Transaction | Span(Bracket) | `Transaction(body)`            | forwards body | atomic boundary: commit the body on success, roll back on failure  |
