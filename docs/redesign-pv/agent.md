# Redesign Agent Guide

This is the entry point for agents implementing the everybase/every_pv redesign.
Read the design docs in this directory first, then use this file for
implementation guidance.

## Design Docs (read in order)

1. `01-vision.md` — Why: PV views have pythonic interfaces, everybase ops
   should work on them directly. Remove duplication from every_pv.
2. `02-primitive-ref-analysis.md` — The item ref question: values vs locations,
   bound/unbound, mutation, and why everybase needs location refs.
3. `03-final-design.md` — THE PLAN: full rename map, package architecture,
   type hierarchy, implementation phases. This is the source of truth.

## Key Concepts

**Type** = WHAT it can do (interface). `IntType` has `+`, `-`, `*`, `>`, etc.
**Value** = typed value holder (RValue). `IntValue(42)` or `IntValue(AddOp(...))`.
**Ref** = typed location pointer (LValue). Points to address in storage.
**Morphism** = transformation (RValue). Operation (pure) or Command (impure).

```
Term[T]
├── LValue[T] → Ref[T]              location pointer
└── RValue[T] → Value[T]            value holder
              → Morphism[T]          transformation
```

Composition: `IntValue = IntType + PyValueBase`. `PVIntRef = IntType + PVPrimitiveRef`.
Types carry the interface. Substrates carry the storage.

## Codebase Map

### everyabc — abstract term algebra
```
abc/everyabc/src/everyabc/
  term/term.py       — Term, LValue, RValue (ADD Value[T] under RValue)
  term/ref.py        — Ref[T] under LValue (unchanged, now correct semantics)
  term/morphism.py   — Morphism, Operation, Command (unchanged)
  context/           — Context, Handle
  __init__.py        — all exports
```

### everybase — types + values + capabilities + morphisms
```
abc/everybase/src/everybase/
  refs/              — RENAME to types/ (IntRefBase → IntType, etc.)
    _base.py         — RefBase → TypeBase
    int.py           — IntRefBase → IntType
    (13 more files, same pattern)

  py/                — Python memory value substrate
    base.py          — PyRefBase → PyValueBase
    refs.py          — RENAME to values.py (IntRef → IntValue, etc.)

  capabilities/      — Protocol + Base pairs (24 files)
    gen_*            — arithmetic, comparison, logical, bitwise
    col_*            — collection reads
    (ADD mut_* for mutations, loc_* for location capabilities)

  morphisms/         — Operations + Commands (18 files)
    op_*, fn_*, gen_*, type_*, abc_*
    (ADD cmd_collection.py for mutation commands)

  __init__.py        — main exports (UPDATE all names)
  utils.py           — ensure_term, typed_ref → typed_value
  combiners.py       — all_, any_, ifelse, coalesce
```

### every_pv — PV storage substrate
```
std/every_pv/src/every_pv/
  ref.py             — PVRefBase, PVPrimitiveRef, PVViewRef (real Refs)
  shape.py           — PVShape, PVShapeMeta, SlotDescriptor
  spans.py           — PVAtomic, PVSnapshot

  pv/primitives.py   — PVIntRef, PVStrRef, PVItemRef, etc.
  pv/collections.py  — PVDictRef, PVListRef, PVShapeRef, etc.

  slots/slots.py     — IntSlot, StrSlot, DictSlot, ListSlot, etc.

  morphisms/         — PV-specific only (DELETE redundant ones)
    core_access.py   — GetOp, ExtractOp, ExistsOp, MissingOp, LengthOp
    core_mutate.py   — SetCmd, DeleteCmd, StoreCmd, ClearCmd, TypedSetCmd
    reactive.py      — OnChangeOp, OnChildChangeOp, OnDescendantsChangeOp
    mapping.py       — DELETE (use everybase abc_mapping + fn_transform)
    sequence.py      — DELETE (use everybase abc_sequence + fn_transform)
    set.py           — DELETE (use everybase abc_set)

  traits/            — DELETE entire directory (use everybase capabilities)
  protocols/         — DELETE entire directory (use everybase protocols)

  __init__.py        — UPDATE exports
```

### every_view — standard view implementations (NO CHANGES)
```
std/every_view/src/every_view/
  (DictView, ListView, SetView, etc. — unchanged)
```

### Reference: original PV library
```
/Users/gor/Projects/everyabc/pv/
  (read-only reference — the upstream PV library every_pv is based on)
```

## Implementation Phases

Execute in order. Each phase should leave tests passing before moving on.

### Phase 1: everyabc — Add Value[T]

Files to change:
- `abc/everyabc/src/everyabc/term/term.py` — add Value[T](RValue[T])
- `abc/everyabc/src/everyabc/__init__.py` — export Value

Value class:
```python
class Value(RValue[T_co], ABC):
    """Typed value holder — literal or computed.

    Values are RValues that hold data directly or wrap a source Term.
    They have no address and cannot be written to.
    """

    @property
    def is_self_pure(self) -> bool:
        return True  # values never have side effects
```

Note: the concrete execute() goes in PyValueBase (everybase), not here.
Value in everyabc is abstract — just establishes the type in the hierarchy.

### Phase 2: everybase — Rename Ref→Type+Value

This is the big rename. Do it mechanically:

1. `refs/` directory → `types/`
   - Rename every file's main class: `IntRefBase` → `IntType`
   - Update `_base.py`: `RefBase` → `TypeBase`
   - Update `__init__.py` in the directory

2. `py/refs.py` → `py/values.py`
   - Rename every class: `IntRef` → `IntValue`
   - Update `py/base.py`: `PyRefBase` → `PyValueBase`
   - PyValueBase should extend Value (from everyabc) instead of Ref
   - Update `py/__init__.py`

3. Update all internal imports across everybase:
   - `capabilities/` — all 24 files reference types like IntRefBase, StrRefBase
   - `morphisms/` — some reference concrete types
   - `utils.py` — typed_ref → typed_value
   - `combiners.py` — may reference types
   - `__init__.py` — the big export file

4. Search for ALL occurrences (these strings appear everywhere):
   - `RefBase` → `TypeBase` (but NOT `PVRefBase` — that stays)
   - `IntRefBase` → `IntType` (and all other type bases)
   - `IntRef` → `IntValue` (and all other concrete values)
   - `PyRefBase` → `PyValueBase`
   - `typed_ref` → `typed_value`
   - Watch out: `Ref` by itself stays (everyabc's Ref is correct)
   - Watch out: PV's refs stay as-is (PVItemRef, PVDictRef, etc.)

5. Run everybase tests: `make test-pkg PKG=abc/everybase`

### Phase 3: everybase — Add mutation commands + capabilities

New files to create:

1. `morphisms/cmd_collection.py`:
   - SetItemCmd(BinaryCommand) — collection[key] = value
   - DeleteItemCmd(UnaryCommand) — del collection[key]
   - AppendCmd(BinaryCommand) — collection.append(value)
   - InsertCmd(TernaryCommand) — collection.insert(index, value)
   - PopCmd(BinaryCommand) — collection.pop(index)
   - ClearCmd(UnaryCommand) — collection.clear()
   - AddCmd(BinaryCommand) — set.add(value)
   - RemoveCmd(BinaryCommand) — set.remove(value)
   - DiscardCmd(BinaryCommand) — set.discard(value)
   - UpdateCmd(BinaryCommand) — collection.update(other)
   All follow the pattern in gen_attr.py (SetAttrOp is a TernaryCommand).

2. Mutation capabilities (mut_*):
   - `mut_indexable_base.py` + `mut_indexable_protocol.py`
   - `mut_sequence_base.py` + `mut_sequence_protocol.py`
   - `mut_mapping_base.py` + `mut_mapping_protocol.py`
   - `mut_set_base.py` + `mut_set_protocol.py`
   - `mut_clearable_base.py` + `mut_clearable_protocol.py`
   Follow existing patterns (e.g., col_sequence_base.py for style).

3. Location capabilities (loc_*):
   - `loc_gettable_base.py` + `loc_gettable_protocol.py`
   - `loc_settable_base.py` + `loc_settable_protocol.py`
   - `loc_existable_base.py` + `loc_existable_protocol.py`
   - `loc_deletable_base.py` + `loc_deletable_protocol.py`
   - `loc_observable_base.py` + `loc_observable_protocol.py`
   These use abstract hooks (_make_get_op, _make_set_cmd, etc.)
   that substrates implement.

4. Extend type bases:
   - ListType: add .append(), .insert(), .pop(), .clear()
   - DictType: add .clear(), .update()
   - SetType: add .add(), .remove(), .discard(), .clear()

5. Update exports and run tests.

### Phase 4: every_pv — Simplify

1. Update ALL imports:
   - `IntRef` → `IntValue`, `StrRef` → `StrValue`, etc.
   - `IntRefBase` → `IntType`, etc.
   - `typed_ref` → `typed_value`

2. Delete redundant files:
   - `traits/` directory (entire thing)
   - `protocols/` directory (entire thing)
   - `morphisms/mapping.py`
   - `morphisms/sequence.py`
   - `morphisms/set.py`

3. Consolidate remaining morphisms:
   - `morphisms/core_access.py` → `morphisms/pv_access.py`
   - `morphisms/core_mutate.py` → `morphisms/pv_mutate.py`
   - `morphisms/reactive.py` stays

4. Update PV ref classes to use everybase capabilities:
   - PVIntRef: `IntType` (was IntRefBase) — just a rename
   - PVDictRef: use everybase MutableMappingBase instead of own traits
   - PVListRef: use everybase MutableSequenceBase instead of own traits
   - PVItemRef: use everybase LocationGettable, LocationSettable, etc.
     implementing hooks with PV-specific morphisms (GetOp, SetCmd)

5. Update `__init__.py` exports.

6. Run every_pv tests: check std/every_pv/tests/

### Phase 5: Tests

1. Update all test files for new names
2. Verify PV views work with everybase operations (functional tests)
3. Run full suite

### Phase 6 (future): every_py — not in scope for this refactor

## Gotchas and Edge Cases

### NoneType clash
Python's builtin `NoneType` conflicts. Use `NoneType_` (with underscore)
for the everybase type base. The value class `NoneValue` is fine.

### PV refs stay as "Ref"
PVItemRef, PVDictRef, PVViewRef — these ARE real Refs (location pointers).
Don't rename them. Only rename everybase's py/ concrete types (IntRef → IntValue).

### _wrap_*_result methods in capability bases
These currently return concrete Ref types (e.g., `IntRef`). Update to return
Value types (e.g., `IntValue`). Search for `_wrap_` in capabilities/.

### ensure_term in utils.py
This converts Python literals to appropriate Value types. Update the mapping:
`int → IntValue`, `str → StrValue`, etc. (was `int → IntRef`, etc.)

### typed_value (was typed_ref)
Used throughout capabilities to wrap operation results in typed values.
Rename and update the type mapping inside.

### every_pv traits/bases_primitive.py and traits/bases_collections.py
These import everybase types. When deleting traits/, make sure the
equivalent functionality exists in everybase capabilities first.
Phase 3 (add capabilities) must complete before Phase 4 (simplify every_pv).

### every_pv morphisms reference everybase types
`morphisms/core_access.py`, `core_mutate.py` etc. import IntRef, StrRef.
Update to IntValue, StrValue, etc. in Phase 4.

### Test files reference old names
Both everybase and every_pv test files use IntRef, DictRef, etc. extensively.
Update all test imports in Phase 2 (everybase) and Phase 5 (every_pv).

### Capabilities reference type bases
All 24 capability files in everybase reference `IntRefBase`, `ListRefBase`, etc.
in their `_wrap_*_result` methods. These all need updating in Phase 2.

## Verification Commands

```bash
# everybase tests
make test-pkg PKG=abc/everybase

# every_pv tests
make test-pkg PKG=std/every_pv

# Check for stale old names (should return 0 matches after refactor)
grep -r "IntRef\b" abc/everybase/src/ --include="*.py"
grep -r "IntRefBase\b" abc/everybase/src/ --include="*.py"
grep -r "PyRefBase\b" abc/everybase/src/ --include="*.py"
grep -r "typed_ref\b" abc/everybase/src/ --include="*.py"

# Check every_pv for stale names
grep -r "IntRef\b" std/every_pv/src/ --include="*.py"
grep -r "IntRefBase\b" std/every_pv/src/ --include="*.py"
```

## Style Notes

- Python 3.10+, ruff for linting (rules in root pyproject.toml)
- No backwards compatibility — break whatever needed
- Never commit as Claude, never mention Claude as co-author
- Check contributing guidelines in ./contributing
- Check docs in ./docs for overall concepts
