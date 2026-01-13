# Storage Layer 1 — Context Model

All storage operations execute inside an explicit **context**.

A context defines:

- what kind of operations are allowed
- what consistency guarantees apply
- how work is isolated and committed

Contexts are **foundational**, not optional.

## Context Types

There are three kinds of contexts:

- **Snapshot** — read-only
- **WriteBatch** — write-only
- **Transaction** — read + write

Each context exposes a constrained command set.

---

## Snapshot (Read-only)

Purpose: consistent, immutable view of storage state.

Allowed operations:

- `get(key) -> Value | EMPTY`
- `exists(key) -> bool`
- `multiget(keys: list[key.Key]) -> dict[key.Key, Value | EMPTY]`
- `scan(...) -> iterator`

Disallowed:

- `put`
- `delete`
- any mutation

Snapshots never modify storage.

---

## WriteBatch (Write-only)

Purpose: staged, atomic mutations.

Allowed operations:

- `put(key, value) -> None`
- `delete(key) -> None`

Disallowed:

- `get`
- `exists`
- `scan`

WriteBatches do not observe storage state.
They only record intended mutations.

---

## Transaction (Read + Write)

Purpose: isolated read–modify–write workflows.

Allowed operations:

- `get(key) -> Value | EMPTY`
- `multiget(keys: list[key.Key]) -> dict[key.Key, Value | EMPTY]`
- `exists(key) -> bool`
- `put(key, value) -> None`
- `delete(key) -> None`
- `scan(...) -> iterator`

Transactions may observe and mutate storage within a single context.

---

## Design Rules

- Context capabilities are **strict**, not advisory
- No operation performs implicit reads or writes
- Missing keys are never exceptional at this layer
- Semantics are identical across backends

Higher layers may adapt these contexts into more ergonomic forms.

---

Contexts are the unit of correctness.
APIs exist to make illegal states unrepresentable.
