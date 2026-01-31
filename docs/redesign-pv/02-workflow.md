# Workflow: Implementing the Vision

## Done

| Phase | What | Branch/Commit |
|-------|------|---------------|
| 1 | everyabc — add Value[T] to term hierarchy | b58359c |
| 2 | everybase — rename Ref→Type+Value (refs/→types/, IntRef→IntValue, IntRefBase→IntType) | d8cf7dc |
| 3 | everybase — add mutation commands + capabilities (abc_sequence, abc_mapping, abc_set, cmd_collection, loc protocols, type base wiring) | 9419a04 |
| 4.1 | every_pv — update imports to new everybase names | staged |

779 tests passing, ruff clean.


## Next: Standardize Substrate Contracts in everybase

Implement the three patterns from vision section 5. Each can be done independently.

### A. Collection Item Access

Add to everybase:

1. **ItemRef base** — abstract ref with parent + address (in `refs/` or `bases/`)
2. **Morphisms** — ItemGetOp, ItemSetCmd, ItemDeleteCmd, ItemExistsOp, ItemMissingOp (new file: `morphisms/loc_item.py`)
3. **Capability bases** — ItemGettableBase, ItemSettableBase, ItemDeletableBase, ItemExistableBase (new file: `capabilities/loc_item.py`)
4. **Wire** — update loc.py protocols to match, export from `__init__.py`

Then in every_pv:

5. PVItemRef, PVListItemRef, PVDictItemRef inherit from everybase's ItemRef base + capability bases
6. Delete PV's custom GettableBase, SettableBase, DeletableBase, ExistableBase from `traits/core.py`
7. Delete PV's GetOp, SetCmd, DeleteCmd, ExistsOp, MissingOp from `morphisms/core_access.py` and `morphisms/core_mutate.py` (keep ExtractOp/StoreCmd until step B)

### B. Extract / Store

Add to everybase:

1. **Protocols** — Convertible, Initializable (new file or extend `capabilities/loc_item.py`)
2. **Morphisms** — ExtractOp, StoreCmd (in `morphisms/loc_item.py` or `morphisms/loc_collection.py`)
3. **Capability bases** — ExtractableBase, StorableBase

Then in every_pv:

4. Delete PV's ExtractOp, StoreCmd, ExtractableBase, StorableBase
5. PV collection refs use everybase bases

### C. Reactivity

Add to everybase:

1. **Subscription protocol** (in `capabilities/loc_reactive.py` or similar)
2. **Observable protocols** — Observable, ChildObservable, ChildrenObservable, DescendantsObservable
3. **Morphisms** — OnChangeOp, OnChildChangeOp, OnChildrenChangeOp, OnDescendantsChangeOp (new file: `morphisms/loc_reactive.py`)
4. **Capability bases** — ObservableBase, ChildObservableBase, ChildrenObservableBase, DescendantsObservableBase

Then in every_pv:

5. Delete PV's reactive morphisms (`morphisms/reactive.py`)
6. Delete PV's observable bases (`traits/observable.py`)
7. PV refs use everybase bases; PV views implement everybase's observable protocols


## Then: Clean Up every_pv

After A+B+C, every_pv's `traits/` and `morphisms/` are mostly empty. Clean up:

1. Delete `protocols/` entirely (redundant with everybase)
2. Delete emptied morphism files, keep only what's truly PV-specific (if anything remains)
3. Delete emptied trait/base files
4. Rename remaining `traits/` → `bases/` if anything survives
5. Clean `__init__.py` exports
6. Remove `UnionRefBases` hack from any remaining files


## Finally: Tests + Downstream

1. Add every_pv tests (shape/slot construction, ref path resolution, morphism construction)
2. Add everybase tests for new item/extract/reactive morphisms
3. Update downstream packages (every_type, every_flow, etc.)
4. Final verification: full test suite + ruff + grep for stale names
