# Span

Transparent Interaction sub-kind. Wraps any Nu (Ref, Query, Command, Flow, or another Span) and yields what its body yields. Sub-shapes: Bracket, Policy.

Partial - samples below to confirm direction.

## Bracket

| Name        | Sub-shape | Signature           | Meaning                               |
| ----------- | --------- | ------------------- | ------------------------------------- |
| Snapshot    | Bracket   | `Snapshot(body)`    | freeze a consistent view for the body |
| Transaction | Bracket   | `Transaction(body)` | commit-or-rollback semantics          |

## Policy

| Name     | Sub-shape | Signature                 | Meaning                          |
| -------- | --------- | ------------------------- | -------------------------------- |
| Retry    | Policy    | `Retry(body, n, ...)`     | retry on failure up to n times   |
| TryCatch | Policy    | `TryCatch(body, handler)` | catch and handle errors          |
| Timeout  | Policy    | `Timeout(body, t)`        | abort if body runs longer than t |
| Throttle | Policy    | `Throttle(body, rate)`    | rate-limit invocations           |
| Debounce | Policy    | `Debounce(body, dt)`      | coalesce rapid invocations       |
