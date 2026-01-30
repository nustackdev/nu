# PV Redesign Workflow

Branch: `refactor/pv-redesign` (from `main` at `48c3b62`)

## Baseline

- everyabc: 238 tests passing
- everybase: 456 tests passing
- every_pv: 0 tests (none exist)
- ruff: clean
- every_type: pre-existing collection errors (out of scope)

## Phases & Commits

### Phase 1: everyabc -- Add Value[T]

**Status: DONE** (commit `b58359c`)

Add `Value[T](RValue[T])` to the term hierarchy as sibling of Morphism.

Commit 1.1: Add Value[T] to everyabc
- `abc/everyabc/src/everyabc/term/term.py` -- add Value class
- `abc/everyabc/src/everyabc/term/__init__.py` -- export Value
- `abc/everyabc/src/everyabc/__init__.py` -- export Value
- Verify: `make test-pkg PKG=abc/everyabc`

---

### Phase 2: everybase -- Rename Ref -> Type + Value

**Status: DONE** (commit `d8cf7dc`)

The big mechanical rename. Split into multiple commits for safety.

Commit 2.1: Rename refs/ -> types/, RefBase -> TypeBase, XxxRefBase -> XxxType
- Rename directory `refs/` -> `types/`
- `types/_base.py` -- RefBase -> TypeBase
- `types/int.py` -- IntRefBase -> IntType (and all 13 type files)
- `types/__init__.py` -- update all exports
- Update all internal imports in capabilities/ (24 files), morphisms/, utils.py, combiners.py
- Verify: `make test-pkg PKG=abc/everybase` (will fail until 2.2)

Commit 2.2: Rename py/ classes: PyRefBase -> PyValueBase, XxxRef -> XxxValue
- `py/base.py` -- PyRefBase -> PyValueBase, inherit from Value (everyabc)
- `py/refs.py` -> `py/values.py` -- IntRef -> IntValue (all 15 classes)
- `py/__init__.py` -- update exports
- Update utils.py: typed_ref -> typed_value, ensure_term mappings
- Update all internal imports
- Verify: `make test-pkg PKG=abc/everybase` (will fail until 2.3)

Commit 2.3: Update everybase __init__.py exports + fix all tests
- `__init__.py` -- update all re-exports to new names
- `tests/` -- update all test files for new names
- Verify: `make test-pkg PKG=abc/everybase` (must pass)
- Verify: `make lint`

---

### Phase 3: everybase -- Add mutation commands + capabilities

**Status: DONE** (commit pending)

New files, no renames. Extends everybase with collection mutations.
Organization: domain-first — ops + cmds merged per collection type in
abc_* files. Mutable capabilities merged into parent col_* files.
Location capabilities are protocol-only (no base — substrates implement).

Morphisms (abc_* -- ops + cmds per collection domain):
- `morphisms/abc_sequence.py` -- FirstOp, LastOp, IndexOfOp, CountOp + AppendCmd, InsertCmd, PopCmd
- `morphisms/abc_mapping.py` -- KeysOp, ValuesOp, ItemsOp, GetOp + SetItemCmd, DeleteItemCmd, UpdateCmd
- `morphisms/abc_set.py` -- UnionOp, IntersectionOp, ... + AddCmd, RemoveCmd, DiscardCmd
- NEW `morphisms/cmd_collection.py` -- ClearCmd (shared across collection types)

Collection capabilities (mutable merged into parent col_* files):
- `capabilities/col_sequence_base.py` -- SequenceBase + MutableSequenceBase
- `capabilities/col_sequence_protocol.py` -- SequenceProtocol + MutableSequenceProtocol
- `capabilities/col_mapping_base.py` -- MappingBase + MutableMappingBase
- `capabilities/col_mapping_protocol.py` -- MappingProtocol + MutableMappingProtocol
- `capabilities/col_set_base.py` -- SetLikeBase + MutableSetBase
- `capabilities/col_set_protocol.py` -- SetLikeProtocol + MutableSetProtocol
- NEW `capabilities/col_clearable_base.py` + `col_clearable_protocol.py`

Location capabilities (protocol-only, no base):
- NEW `capabilities/loc_gettable_protocol.py` -- LocationGettableProtocol
- NEW `capabilities/loc_settable_protocol.py` -- LocationSettableProtocol
- NEW `capabilities/loc_existable_protocol.py` -- LocationExistableProtocol
- NEW `capabilities/loc_deletable_protocol.py` -- LocationDeletableProtocol
- NEW `capabilities/loc_observable_protocol.py` -- LocationObservableProtocol

Type bases wired to mutable capabilities:
- `types/list.py` -- ListType: MutableSequenceBase + ClearableBase
- `types/dict.py` -- DictType: MutableMappingBase + ClearableBase
- `types/set.py` -- SetType: MutableSetBase + ClearableBase

Tests: NEW `tests/unit/test_mutations.py` -- 42 tests
- Verify: 497 tests passing, lint clean

---

### Phase 4: every_pv -- Simplify

**Status: PENDING**

Update imports, delete redundant code, wire to everybase capabilities.

Commit 4.1: Update every_pv imports to new everybase names
- All files in `std/every_pv/src/every_pv/` -- IntRef -> IntValue, etc.
- IntRefBase -> IntType, etc.
- typed_ref -> typed_value
- Verify: import works

Commit 4.2: Delete redundant every_pv code
- DELETE `traits/` directory (use everybase capabilities)
- DELETE `protocols/` directory (use everybase capability protocols)
- DELETE `morphisms/mapping.py` (use everybase abc_mapping)
- DELETE `morphisms/sequence.py` (use everybase abc_sequence)
- DELETE `morphisms/set.py` (use everybase abc_set)
- Verify: import works

Commit 4.3: Consolidate remaining PV morphisms
- `morphisms/core_access.py` -> `morphisms/pv_access.py`
- `morphisms/core_mutate.py` -> `morphisms/pv_mutate.py`
- `morphisms/reactive.py` stays
- Update `morphisms/__init__.py`
- Update `__init__.py`
- Verify: `make lint`

Commit 4.4: Wire PV refs to everybase capabilities
- `pv/collections.py` -- PVDictRef uses MutableMappingBase, etc.
- `pv/primitives.py` -- PVItemRef uses location capabilities
- Update `__init__.py` exports
- Verify: `make lint`

---

### Phase 5: Tests + downstream updates

**Status: PENDING**

Commit 5.1: Update every_type imports
- `std/every_type/src/every_type/` -- all XxxRef -> XxxValue, XxxRefBase -> XxxType

Commit 5.2: Update every_flow, every_adapters, every_notion if they reference old names
- grep for old names across std/ and pkgs/

Commit 5.3: Final verification
- `make test` (full suite)
- `make lint`
- grep for stale names (IntRef, IntRefBase, PyRefBase, typed_ref) in src/

---

## Verification Commands

```bash
# Per-package tests
make test-pkg PKG=abc/everyabc
make test-pkg PKG=abc/everybase
make test-pkg PKG=std/every_pv

# Lint
make lint

# Stale name checks (should return 0 after Phase 2+)
grep -r "IntRef\b" abc/everybase/src/ --include="*.py"
grep -r "IntRefBase\b" abc/everybase/src/ --include="*.py"
grep -r "PyRefBase\b" abc/everybase/src/ --include="*.py"
grep -r "typed_ref\b" abc/everybase/src/ --include="*.py"

# After Phase 4 -- check every_pv too
grep -r "IntRef\b" std/every_pv/src/ --include="*.py"
grep -r "IntRefBase\b" std/every_pv/src/ --include="*.py"
```

## Session Resume Notes

When resuming:
1. Read this file first to check current phase status
2. Check `git log --oneline -20` on `refactor/pv-redesign` branch
3. Run the verification command for the current phase
4. Pick up from the next PENDING commit
