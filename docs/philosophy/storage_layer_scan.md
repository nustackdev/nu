# Storage Layer 1 — Scan Operation

`scan` provides ordered, streaming access to key ranges.

It is a **system-level iteration primitive**, not a collection.

## Availability

`scan` is supported in:

- Snapshot
- Transaction

`scan` is not supported in:

- WriteBatch

## Semantics

- Iteration is backend-driven
- Results are streamed, not materialized
- Order follows the storage engine’s native key order
- No guarantees beyond the active context

## Constraints

- `scan` does not imply isolation beyond the context
- `scan` does not observe uncommitted writes outside the context
- `scan` performs no implicit buffering or retries

## Role

`scan` exists to:

- traverse keyspaces
- power higher-level iteration utilities
- expose backend iteration without abstraction leaks

Any stronger guarantees belong in higher layers.
