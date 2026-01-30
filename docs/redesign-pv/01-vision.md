# every_pv Redesign Vision

## Core Insight

PV views have 1:1 pythonic interfaces (`DictView.__getitem__`, `ListView.append`,
`SetView.add`, etc.), and everybase capabilities (`MappingBase`, `SequenceBase`,
`SetLikeBase`) map to the same Python collection ABCs. This means:

**PV collection refs can resolve to view objects, and everybase operations work
on them directly.**

```
PVDictRef.fetch(ctx) -> DictView
                            |
     everybase KeysOp -> list(view.keys())     ok
     everybase AtOp   -> view["key"]           ok
     everybase MapOp  -> map(fn, view)         ok
     new SetItemCmd   -> view["key"] = value   ok
```

## What everybase already has vs what it lacks

### Has (pure operations)

- All arithmetic, comparison, logical, bitwise ops
- Collection reads: `AtOp`, `LenOp`, `ContainsOp`, `KeysOp`, `ValuesOp`, `ItemsOp`
- Higher-order: `MapOp`, `FilterOp`, `ReduceOp`, `SortedOp`, `FindOp`
- Sequence: `FirstOp`, `LastOp`, `IndexOfOp`, `CountOp`
- Set algebra: `UnionOp`, `IntersectionOp`, `DifferenceOp`, etc.
- Attribute: `SetAttrOp`, `DelAttrOp` (already Commands)

### Lacks (collection mutation commands)

- `SetItemCmd(container, key, value)` -> `container[key] = value`
- `DeleteItemCmd(container, key)` -> `del container[key]`
- `AppendCmd(container, value)` -> `container.append(value)`
- `InsertCmd(container, index, value)` -> `container.insert(index, value)`
- `PopCmd(container, index?)` -> `container.pop(index)`
- `ClearCmd(container)` -> `container.clear()`
- `AddCmd(container, value)` -> `container.add(value)` (sets)
- `RemoveCmd(container, value)` -> `container.remove(value)` (sets)
- `DiscardCmd(container, value)` -> `container.discard(value)` (sets)
- `UpdateCmd(container, other)` -> `container.update(other)` (dicts/sets)

The Operation/Command distinction already exists in everyabc (`morphism.py`
has `UnaryCommand`, `BinaryCommand`, `TernaryCommand`). everybase just hasn't
used it beyond `SetAttrOp`/`DelAttrOp`.

## What every_pv currently duplicates (to remove)

| every_pv morphism | everybase equivalent |
|---|---|
| `morphisms/sequence.py` MapOp, FilterOp, ReduceOp, etc. | `fn_transform.py`, `fn_search.py` |
| `morphisms/mapping.py` KeysOp, ValuesOp, ItemsOp, etc. | `abc_mapping.py`, `fn_transform.py` |
| `morphisms/sequence.py` IndexOfValueOp, CountOfValueOp | `abc_sequence.py` |
| `traits/sequence.py`, `traits/mapping.py`, `traits/set.py` | `capabilities/col_*.py` |
| `protocols/capabilities.py` | everybase capability protocols |

## What's unique to every_pv (must keep)

1. **`ref.py`** - PV ref bases (fetch/resolve - the substrate)
2. **`shape.py`** - Shape system (PVShape, SlotDescriptor, PVShapeMeta)
3. **`spans.py`** - PVAtomic, PVSnapshot (transaction/snapshot boundaries)
4. **`morphisms/` (PV-specific only)**:
   - ExtractOp (view.extract()), ExistsOp, MissingOp
   - StoreCmd (view.store()), TypedSetCmd
   - Reactive: OnChangeOp, OnChildChangeOp, OnDescendantsChangeOp
5. **`slots/`** - Slot factories (ItemSlot, DictSlot, ListSlot, ShapeSlot)

## Proposed architecture

```
everybase (term layer) - EXTENDED
  capabilities/
    gen_*              # existing: arithmetic, comparison, logical, bitwise
    col_*              # existing: containable, lengthable, indexable, iterable
    col_sequence.py    # existing: SequenceBase (reads)
    col_mapping.py     # existing: MappingBase (reads)
    col_set.py         # existing: SetLikeBase (reads)
    NEW: mut_indexable.py   # MutableIndexableBase (__setitem__, __delitem__)
    NEW: mut_sequence.py    # MutableSequenceBase (append, insert, pop)
    NEW: mut_mapping.py     # MutableMappingBase (update, setdefault)
    NEW: mut_set.py         # MutableSetBase (add, remove, discard)
    NEW: mut_clearable.py   # ClearableBase
  morphisms/
    op_*, fn_*, gen_*, type_*, abc_*  # existing operations
    NEW: cmd_collection.py  # Generic mutation commands
  refs/
    existing bases...
    EXTENDED: mutable collection bases in list.py, dict.py, set.py

every_pv (PV substrate) - SIMPLIFIED
  ref.py                 # PV ref bases (fetch/resolve - the substrate)
  shape.py               # Shape system
  spans.py               # PVAtomic, PVSnapshot
  pv/
    primitives.py        # PVIntRef = PVPrimitiveRef[int] + IntRefBase
    collections.py       # PVDictRef = PVViewRef + MutableMappingRefBase
  slots/                 # Shape slot factories
  morphisms/             # ONLY PV-specific morphisms
    pv_access.py         # ExtractOp, ExistsOp, MissingOp
    pv_mutate.py         # StoreCmd, TypedSetCmd
    reactive.py          # OnChangeOp, OnChildChangeOp, etc.
  REMOVED: traits/, protocols/, redundant morphisms
```

## Execution order

1. Add command morphisms to everybase (cmd_collection.py)
2. Add mutation capabilities to everybase (mut_*.py)
3. Extend ref bases with mutable variants
4. Simplify every_pv - remove redundant morphisms/traits/protocols
5. Verify PV view iteration works with everybase higher-order ops
6. Polish naming, exports, tests

## What this achieves

- every_pv becomes a thin substrate layer (refs, shapes, spans, PV-specific ops)
- everybase becomes single source of collection operations (reads AND writes)
- Mutation is first-class in everybase, not bolted on per-substrate
- Any future substrate just needs fetch() returning a pythonic object
