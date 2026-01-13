# DX Ergonoics Philosophy for Storage Layer

This layer is a **system interface**, not a Python container.

It represents a storage engine (RocksDB, LMDB, etc.), not a python data structure.
APIs are designed around **idempotent commands and status-based reads**, not container invariants.

## Core Principles

- Missing keys are **normal**, not exceptional
- Writes and deletes are **commands**, not queries
- Errors represent **operational failure**, not data absence
- Backend differences are absorbed here; callers see one model

## API Semantics

### Reads

- `get(key) -> Value | EMPTY`

  - Never raises for missing keys
  - Uses an explicit sentinel (`EMPTY`) to avoid ambiguity

- `exists(key) -> bool`

  - Explicit existence check
  - No side effects

### Writes

- `put(key, value) -> None`

  - Create or overwrite
  - Raises only on real failure (IO, corruption, closed DB)

### Deletes

- `delete(key) -> None`

  - Silent and idempotent
  - No signal about prior existence
  - Raises only on real failure

## Naming Conventions

- `get / put / delete / exists` reflect **system verbs**
- No `__getitem__`, `pop`, `remove`, or `del`
- No boolean-returning mutations
- No exceptions for missing keys

## Non-Goals

- Not dict-like
- Not exception-driven
- Not responsible for user-facing ergonomics

Container-style behavior (KeyError, `in`, `del obj[key]`) belongs in a higher adapter layer.

---

This layer exists to be **boring, explicit, and swappable**.

Other operations should follow the same logic (scan, multi get, etc...).
