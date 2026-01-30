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

**Status: PENDING**

Add `Value[T](RValue[T])` to the term hierarchy as sibling of Morphism.

Commit 1.1: Add Value[T] to everyabc
- `abc/everyabc/src/everyabc/term/term.py` -- add Value class
- `abc/everyabc/src/everyabc/term/__init__.py` -- export Value
- `abc/everyabc/src/everyabc/__init__.py` -- export Value
- Verify: `make test-pkg PKG=abc/everyabc`

---

### Phase 2: everybase -- Rename Ref -> Type + Value

**Status: PENDING**

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

**Status: PENDING**

New files, no renames. Extends everybase with collection mutations.

Commit 3.1: Add cmd_collection.py (mutation commands)
- NEW `morphisms/cmd_collection.py` -- SetItemCmd, DeleteItemCmd, AppendCmd,
  InsertCmd, PopCmd, ClearCmd, AddCmd, RemoveCmd, DiscardCmd, UpdateCmd
- `morphisms/__init__.py` -- export new commands
- `__init__.py` -- export new commands
- Verify: `make test-pkg PKG=abc/everybase`

Commit 3.2: Add mutation capabilities (mut_*)
- NEW `capabilities/mut_indexable_base.py` + `mut_indexable_protocol.py`
- NEW `capabilities/mut_sequence_base.py` + `mut_sequence_protocol.py`
- NEW `capabilities/mut_mapping_base.py` + `mut_mapping_protocol.py`
- NEW `capabilities/mut_set_base.py` + `mut_set_protocol.py`
- NEW `capabilities/mut_clearable_base.py` + `mut_clearable_protocol.py`
- `capabilities/__init__.py` -- export new capabilities
- `__init__.py` -- export new capabilities
- Verify: `make test-pkg PKG=abc/everybase`

Commit 3.3: Add location capabilities (loc_*)
- NEW `capabilities/loc_gettable_base.py` + `loc_gettable_protocol.py`
- NEW `capabilities/loc_settable_base.py` + `loc_settable_protocol.py`
- NEW `capabilities/loc_existable_base.py` + `loc_existable_protocol.py`
- NEW `capabilities/loc_deletable_base.py` + `loc_deletable_protocol.py`
- NEW `capabilities/loc_observable_base.py` + `loc_observable_protocol.py`
- `capabilities/__init__.py` -- export
- `__init__.py` -- export
- Verify: `make test-pkg PKG=abc/everybase`

Commit 3.4: Extend type bases with mutation methods
- `types/list.py` -- ListType: add .append(), .insert(), .pop(), .clear()
- `types/dict.py` -- DictType: add .clear(), .update()
- `types/set.py` -- SetType: add .add(), .remove(), .discard(), .clear()
- Add tests for mutation methods
- Verify: `make test-pkg PKG=abc/everybase`
- Verify: `make lint`

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
