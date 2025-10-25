## rwrocks Transaction/Snapshot Support Roadmap

This document captures everything the next engineer/agent needs to add RocksDB transaction + snapshot bindings to `rwrocks`. The project currently wraps the basic `rocksdb::DB` API; none of the transaction utilities are exposed yet.

### Target Environment

- RocksDB **6.x** headers/libs are present on the system (Homebrew installs them on macOS at `/usr/local/include/rocksdb` by default).
- Use the **uv virtual environment** for builds/tests: `uv pip install -e .`.
- The C extension lives in `src/rwrocks/lib_rocksdb.pyx` with matching `.pxd` definitions.
- Make sure to delete cache and build from ground the c extensions for testing changes.

### High-level Goals

1. Surface transaction-related C++ types and enums in `.pxd` files.
2. Implement Python-visible `TransactionDB` + `Transaction` classes (with option structs) in `lib_rocksdb.pyx`.
3. Update type stubs/exports so downstream users see the new API.
4. Provide a playground demo and automated tests covering the transaction workflow.

### Detailed Work Items

#### 1. C/C++ Exposure (`.pxd` layer)

- Create `src/rwrocks/transaction.pxd` for:
  - `rocksdb::TransactionDBOptions`, `TransactionOptions`, `TransactionDB`, `Transaction`, `TxnDBWritePolicy`, etc.
  - Helper functions for the overloaded `TransactionDB::Open` signatures (with/without column families).
- Update `lib_rocksdb.pxd`:
  - Declare `TransactionDBOptions`, `TransactionOptions`, `Transaction`, `TransactionDB` classes for Python use.
  - Extend iterator structs to track their owning object (plain DB vs. transaction) to avoid dangling pointers.
  - Ensure any new enums/constants are exported similarly to existing option enums.

#### 2. Cython Implementation (`lib_rocksdb.pyx`)

- Add wrappers mirroring the existing `Options`/`ColumnFamilyOptions` approach:
  - `TransactionDBOptions` and `TransactionOptions` with Python properties for each relevant RocksDB field (lock timeouts, write policy, etc.).
  - Python `Transaction` class implementing:
    - Lifecycle (`commit`, `rollback`, `close`, `prepare`, savepoints, `set_snapshot`, etc.).
    - CRUD (`put`, `merge`, `delete`), reads (`get`, `multi_get`), iterators (`iterkeys`, `itervalues`, `iteritems`).
    - Snapshot helpers (return a `Snapshot` object or `None` if unset).
    - Under-the-hood pointer ownership so the transaction and column-family handles stay valid until close.
  - Python `TransactionDB` class:
    - Constructor takes `Options`, optional `TransactionDBOptions`, column-family map.
    - Calls the correct `TransactionDB::Open` overload and stores both `DB*` and `TransactionDB*`.
    - Overrides `begin_transaction` to return the new `Transaction` wrapper, passing through optional `TransactionOptions` and write options (`sync`, `disable_wal`).
    - Respects existing info-log/comparator/table-factory injection logic.
- Refactor iterator classes if needed so they can work with transaction-owned iterators without freeing memory prematurely.

#### 3. Python API Surface & Stubs

- Export the new classes/enums in `src/rwrocks/__init__.py`.
- Update `src/rwrocks/lib_rocksdb.pyi` with accurate type hints for:
  - `TransactionDBOptions`, `TransactionOptions`, `Transaction`, `TransactionDB`, relevant methods and return types.
  - Transaction-aware iterators.
- Document transaction usage (basic sample) in README or a dedicated doc.

#### 4. Demos & Tests

- Add a playground script (e.g., `_playground/transaction_demo.py`) showing:
  - Opening `TransactionDB`.
  - Basic transaction cycle: put, commit, rollback, savepoint, snapshot read.
  - Iterating over keys inside a transaction.
- Extend `tests/` with integration coverage:
  - Successful commit/rollback.
  - Snapshot visibility (data available/hidden depending on commit).
  - Iterator traversal inside a transaction.
  - Basic conflict detection scenario if feasible.
- Run `uv pip install -e .` (build) and `pytest` (or targeted test command) to validate.

### Pitfalls & Notes

- **Overloaded `TransactionDB::Open`**: the multi-arg overload returning CF handles needs a helper shim or exact signature to compile in Cython.
- **Lifetime management**: make sure transactions keep references to the owning `TransactionDB` and column-family handles to avoid use-after-free.
- **Iterator reuse**: existing iterators assume ownership of `Iterator*`; any new constructors must follow that pattern.
- **Thread safety**: RocksDB callbacks may occur on background threads—reuse the existing GIL-handling patterns.
- **Type stubs**: keep them in sync so editors/tests don’t break.

### Deliverables Checklist

- [ ] `transaction.pxd` added with complete C++ exposure.
- [ ] `lib_rocksdb.pxd`/`.pyx` updated with new classes and iterator support.
- [ ] Type hints and `__init__` exports updated.
- [ ] Playground demo and documentation added.
- [ ] Automated tests covering transaction flows.
- [ ] Build/test scripts verified in the uv environment.

Use this plan as the starting point for implementation—each bullet should translate into discrete PR-sized tasks for the next agent. Good luck!
