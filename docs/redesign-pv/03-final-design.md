# Final Design: Value/Ref Split + every_pv Simplification

## The Core Rename

What we called "Ref" was actually "Value". Real Refs are location pointers.

```
BEFORE (confused):
  IntRef(42)              ← called "Ref" but it's a value
  DictRef({"a": 1})       ← called "Ref" but it's a value
  PVItemRef("age")        ← an actual reference (location pointer)

AFTER (correct):
  IntValue(42)            ← value (literal or computed)
  DictValue({"a": 1})     ← value
  DictItemRef("age", d)   ← ref: points to d["age"], has .get()/.set()
  PVItemRef("age")        ← ref: points to PV storage location
```

## Type Hierarchy (everyabc)

```
Term[T]                          — executable node
├── LValue[T]                    — addressable location
│   └── Ref[T]                   — typed location reference
│       resolve(ctx) → Location   (meaningful address)
│       fetch(ctx) → T            (reads from address)
│       + location capabilities: .get(), .set(), .exists(), .remove()
│
└── RValue[T]                    — produces a value
    ├── Value[T]                 — typed value holder
    │   execute(ctx) → T          (return literal or evaluate source)
    │
    └── Morphism[T]              — transformation
        ├── Operation            — pure (no side effects)
        └── Command              — impure (has side effects)
```

Two branches, matching PL theory:
- LValue: has an address (resolve), can be read (fetch) and written (.set)
- RValue: produces a value when evaluated
  - Value: holds a literal or wraps a source Term
  - Morphism: computes a result from operands

Value does NOT need resolve() or fetch() — those are LValue/Ref concerns.
Value just needs execute(): return literal or evaluate source. Simpler.

Operations take Term[T] — accept both Value[int] and Ref[int] as operands.
When a Ref is used as operand, execute() calls fetch() — implicit dereference.

## Package Architecture

### everyabc (abstract layer) — UPDATED

```
src/everyabc/
  term/
    term.py          Value[T] ADDED under RValue
    ref.py           Ref[T] stays under LValue — now truly means "location reference"
    morphism.py      unchanged (Operation/Command, also under RValue)
  context/           unchanged
  tree/              unchanged
```

Changes:
- Add Value[T](RValue[T]) — typed value holder with execute()
  - No resolve(), no fetch() — those are LValue/Ref concerns
  - execute() returns literal or evaluates source Term
  - is_self_pure = True (values never have side effects)
- Ref stays under LValue — now semantically correct
- Shape, Slot, Flow, Span, Context unchanged

### everybase (base layer) — RENAMED + EXTENDED

```
src/everybase/
  __init__.py               updated exports

  types/                    WAS refs/ — type interfaces (the WHAT)
    _base.py                TypeBase[T] (was RefBase[T])
    int.py                  IntType (was IntRefBase)
    float.py                FloatType (was FloatRefBase)
    bool.py                 BoolType (was BoolRefBase)
    str.py                  StrType (was StrRefBase)
    bytes.py                BytesType (was BytesRefBase)
    list.py                 ListType (was ListRefBase)
    dict.py                 DictType (was DictRefBase)
    set.py                  SetType (was SetRefBase)
    frozenset.py            FrozenSetType (was FrozenSetRefBase)
    tuple.py                TupleType (was TupleRefBase)
    any.py                  AnyType (was AnyRefBase)
    none.py                 NoneType_ (was NoneRefBase, underscore avoids builtin clash)
    sentinel.py             SentinelType (was SentinelRefBase)

  py/                       Python memory VALUE substrate
    base.py                 PyValueBase (was PyRefBase)
    values.py               WAS refs.py — concrete value types:
                              IntValue (was IntRef)
                              FloatValue (was FloatRef)
                              BoolValue (was BoolRef)
                              StrValue (was StrRef)
                              BytesValue (was BytesRef)
                              ListValue (was ListRef)
                              DictValue (was DictRef)
                              SetValue (was SetRef)
                              FrozenSetValue (was FrozenSetRef)
                              TupleValue (was TupleRef)
                              AnyValue (was AnyRef)
                              NoneValue (was NoneRef)
                              SentinelValue (was SentinelRef)
                              EmptyValue (was EmptyRef)
                              InvalidValue (was InvalidRef)

  capabilities/             Protocol + Base pairs
    gen_arithmetic_*        unchanged
    gen_comparison_*        unchanged
    gen_logical_*           unchanged
    gen_bitwise_*           unchanged
    col_atoms_*             unchanged
    col_collection_*        unchanged
    col_iterable_*          unchanged
    col_sequence_*          unchanged
    col_mapping_*           unchanged
    col_set_*               unchanged
    NEW: mut_indexable_*    MutableIndexable (__setitem__, __delitem__)
    NEW: mut_sequence_*     MutableSequence (append, insert, pop)
    NEW: mut_mapping_*      MutableMapping (update, setdefault)
    NEW: mut_set_*          MutableSet (add, remove, discard)
    NEW: mut_clearable_*    Clearable (clear)
    NEW: loc_gettable_*     LocationGettable (.get() via hook)
    NEW: loc_settable_*     LocationSettable (.set() via hook)
    NEW: loc_existable_*    LocationExistable (.exists()/.missing() via hook)
    NEW: loc_deletable_*    LocationDeletable (.remove() via hook)
    NEW: loc_observable_*   LocationObservable (.on_change() via hook)

  morphisms/                Operations + Commands
    op_arithmetic.py        unchanged
    op_comparison.py        unchanged
    op_logical.py           unchanged
    op_bitwise.py           unchanged
    fn_transform.py         unchanged
    fn_search.py            unchanged
    fn_aggregate.py         unchanged
    fn_conversion.py        unchanged
    fn_call.py              unchanged
    gen_access.py           unchanged
    gen_attr.py             unchanged (SetAttrOp, DelAttrOp stay as commands)
    gen_conditional.py      unchanged
    gen_special.py          unchanged
    type_str.py             unchanged
    type_bytes.py           unchanged
    abc_mapping.py          unchanged
    abc_sequence.py         unchanged
    abc_set.py              unchanged
    NEW: cmd_collection.py  Mutation commands:
                              SetItemCmd    — collection[key] = value
                              DeleteItemCmd — del collection[key]
                              AppendCmd     — collection.append(value)
                              InsertCmd     — collection.insert(index, value)
                              PopCmd        — collection.pop(index)
                              ClearCmd      — collection.clear()
                              AddCmd        — collection.add(value)
                              RemoveCmd     — collection.remove(value)
                              DiscardCmd    — collection.discard(value)
                              UpdateCmd     — collection.update(other)

  combiners.py              unchanged
  utils.py                  ensure_term, typed_value (was typed_ref)
```

### every_pv (PV substrate) — SIMPLIFIED

```
src/every_pv/
  __init__.py               updated exports

  ref.py                    PVRefBase, PVPrimitiveRef, PVViewRef
                            (these ARE real Refs — location pointers)

  shape.py                  PVShape, PVShapeMeta, SlotDescriptor
  spans.py                  PVAtomic, PVSnapshot

  pv/
    primitives.py           PVIntRef (PVPrimitiveRef + IntBase)
                            PVStrRef, PVFloatRef, PVBoolRef, PVBytesRef
                            PVItemRef, PVListItemRef, PVDictItemRef

    collections.py          PVDictRef (PVViewRef + MutableMappingBase)
                            PVListRef, PVShapeRef, PVShapesListRef, PVShapesDictRef

  slots/
    slots.py                IntSlot, StrSlot, DictSlot, ListSlot, etc.

  morphisms/                ONLY PV-specific morphisms
    pv_access.py            ExtractOp, ExistsOp, MissingOp, LengthOp
    pv_mutate.py            SetCmd, DeleteCmd, StoreCmd, ClearCmd, TypedSetCmd
    reactive.py             OnChangeOp, OnChildChangeOp, OnDescendantsChangeOp

  DELETED: traits/          → everybase capabilities
  DELETED: protocols/       → everybase capability protocols
  DELETED: morphisms/mapping.py, sequence.py, set.py  → everybase morphisms
```

### every_py (NEW, future — Py ref substrate)

```
src/every_py/
  __init__.py

  ref.py                    PyRefBase — location ref for Python dicts
                            (has meaningful resolve: key in dict)

  shape.py                  PyShape, PyShapeMeta

  slots.py                  PyIntSlot, PyStrSlot, PyFloatSlot, etc.

  refs/
    items.py                DictItemRef, ListItemRef, SetItemRef
    collections.py          PyDictRef, PyListRef, PySetRef
                            (mutable collection location refs)
```

## Rename Map (complete)

### everyabc
```
NEW: Value[T]              — Term subclass, typed value holder
Ref[T]                     — stays, now truly means "location reference"
```

### everybase types (refs/ → types/)

Type = the interface (WHAT it can do). Substrate-agnostic.
Composed with Value or Ref base to get a concrete class.

```
RefBase          → TypeBase
IntRefBase       → IntType
FloatRefBase     → FloatType
BoolRefBase      → BoolType
StrRefBase       → StrType
BytesRefBase     → BytesType
ListRefBase      → ListType
DictRefBase      → DictType
SetRefBase       → SetType
FrozenSetRefBase → FrozenSetType
TupleRefBase     → TupleType
AnyRefBase       → AnyType
NoneRefBase      → NoneType_  (underscore avoids builtin clash)
SentinelRefBase  → SentinelType
EmptyRefBase     → EmptyType
InvalidRefBase   → InvalidType
```

Composition pattern:
```python
# Type defines the interface (WHAT)
class IntType(Arithmetic, Comparable, Logical, Bitwise): ...

# Substrate defines storage (WHERE)
class IntValue(IntType, PyValueBase[int]): ...         # literal/computed
class PVIntRef(IntType, PVPrimitiveRef[int]): ...      # PV storage
class PyIntRef(IntType, PyRefBase[int]): ...            # Py dict location

# User-defined types follow the same pattern:
class MoneyType(Arithmetic, Comparable): ...            # custom interface
class MoneyValue(MoneyType, PyValueBase[Money]): ...    # value
class PVMoneyRef(MoneyType, PVPrimitiveRef[Money]): ... # PV ref
```

### everybase concrete types (py/)
```
PyRefBase   → PyValueBase
IntRef      → IntValue
FloatRef    → FloatValue
BoolRef     → BoolValue
StrRef      → StrValue
BytesRef    → BytesValue
ListRef     → ListValue
DictRef     → DictValue
SetRef      → SetValue
FrozenSetRef → FrozenSetValue
TupleRef    → TupleValue
AnyRef      → AnyValue
NoneRef     → NoneValue
SentinelRef → SentinelValue
EmptyRef    → EmptyValue
InvalidRef  → InvalidValue
```

### everybase utilities
```
typed_ref()  → typed_value()
ensure_term  → unchanged (converts literals to Values)
```

### every_pv (imports updated)
```
All imports of IntRef, StrRef, etc. → IntValue, StrValue, etc.
All imports of IntRefBase, etc. → IntBase, etc.
PVItemRef, PVDictRef, PVViewRef — unchanged (these ARE Refs)
```

## Ergonomic Interface: Shared Operators on Values and Refs

Both Values and Refs mix in the same capability bases (IntBase, StrBase, etc.),
so they share the same operator interface:

```python
class IntValue(PyValueBase[int], IntBase): ...   # value
class PVIntRef(PVPrimitiveRef[int], IntBase): ... # PV ref
class DictItemIntRef(DictItemRef[int], IntBase): ... # Py ref
```

All three get +, -, *, >, <, ==, etc. from IntBase. No .get() needed:

```python
Person.age + 10          # works — IntBase.__add__ on the ref
Person.age > 12          # works — IntBase.__gt__ on the ref
AppState.age * 2 + 1     # works — chains naturally
```

When used as operand in an operation, execute() is called:
- Value: returns literal or evaluates source
- Ref: reads from address (implicit dereference)

Result of operations is always a Value (not a Ref):
```python
Person.age + 10    # → IntValue(AddOp(Person.age, IntValue(10)))
                   #   result is a value, not a location
```

Only collection indexing and shape access create Refs:
```python
d["key"]           # → DictItemRef (location)
Person.age         # → DictItemRef via Shape (location)
Person.age + 10    # → IntValue (computed value, not a location)
```

.get() still exists but is optional — only needed to explicitly convert
a Ref to a Value (e.g. to store the value somewhere else). Like explicit
*ptr in C when auto-deref would work.

The ONLY methods unique to Refs (not on Values):
- .set(v), .exists(), .missing(), .remove(), .on_change()
These are location operations that don't make sense on anonymous values.

## Execution Flow Examples

### Pure computation (values only)
```python
x = IntValue(5)
y = IntValue(3)
z = x + y                    # → IntValue(AddOp(x, y))
await z.execute(ctx)          # → 8
```

### PV storage (refs + values)
```python
class AppState(PVShape):
    name = StrSlot()
    age = IntSlot()

# AppState.age → PVItemRef (a real Ref — location in PV storage)
# AppState.age.get() → IntValue(GetOp(self)) — value from location
# AppState.age.set(30) → IntValue(SetCmd(self, IntValue(30))) — write command

PVAtomic(AppState, DictView, Seq(
    AppState.name.set("Alice"),     # SetCmd → writes to PV storage
    AppState.age.set(30),           # SetCmd → writes to PV storage
)).execute(ctx)

result = await (AppState.age.get() + 10).execute(ctx)  # → 40
```

### Python memory (future every_py)
```python
class Person(PyShape):
    name = PyStrSlot()
    age = PyIntSlot()

state = DictValue({"name": "Alice", "age": 30})
ctx = Context().with_handle(dict, state, shape=Person)

# Person.age → DictItemRef("age", parent=backing) — a real Ref
# Person.age.get() → IntValue(AtOp(backing, "age")) — value from location
# Person.age.set(31) → IntValue(SetItemCmd(backing, "age", 31)) — write command

await Person.age.get().execute(ctx)           # → 30
await Person.age.set(31).execute(ctx)         # → 31
await (Person.age.get() + 10).execute(ctx)    # → 41

# Collection mutation:
tags = ListValue(["a", "b"])
await tags.append("c").execute(ctx)           # → ["a", "b", "c"]
await tags[0].set("z").execute(ctx)           # → tags[0] = "z"
```

## What Each Package Owns

```
everyabc — abstract term algebra
  Value[T], Ref[T], Morphism[T], Operation, Command
  Shape, Slot, Context, Flow, Span

everybase — types + values + capabilities + morphisms
  Types:           IntType, DictType, ListType, ...
                   (the WHAT — interface, substrate-agnostic)
  Concrete values: IntValue, DictValue, ListValue, ...
                   (Type + PyValueBase — literal/computed values)
  Capabilities:    arithmetic, comparison, logical, bitwise,
                   collection reads, collection mutations, location ops
  Morphisms:       all operations + commands (pure and impure)
  Combiners:       all_, any_, ifelse, coalesce, ...

every_pv — PV storage substrate (location refs for KV-backed views)
  PV refs:         PVItemRef, PVDictRef, PVViewRef, ...
  PV shapes:       PVShape, Slots
  PV spans:        PVAtomic, PVSnapshot
  PV morphisms:    Extract, Store, Observe (PV-specific only)

every_py — Python memory substrate (location refs for dicts, future)
  Py refs:         DictItemRef, ListItemRef, ...
  Py shapes:       PyShape, Slots
  (lightweight alternative to PV for in-memory use)
```

## Implementation Order

### Phase 1: everyabc — Add Value[T]
1. Add Value[T](RValue[T]) to term.py — sibling of Morphism under RValue
2. Value has execute() only — no resolve(), no fetch()
3. Ref stays under LValue, unchanged
4. Update exports

### Phase 2: everybase — Rename Ref→Type+Value
1. Rename refs/ → types/, RefBase → TypeBase, IntRefBase → IntType, etc.
2. Rename py/refs.py → py/values.py, IntRef → IntValue, etc.
3. Rename py/base.py: PyRefBase → PyValueBase
4. Update all internal imports
5. Update __init__.py exports
6. Update utils: typed_ref → typed_value
7. Update all capabilities and morphisms that reference old names

### Phase 3: everybase — Add mutation commands
1. Add cmd_collection.py with SetItemCmd, DeleteItemCmd, AppendCmd, etc.
2. Add mutation capabilities: mut_indexable, mut_sequence, mut_mapping, mut_set
3. Add location capabilities: loc_gettable, loc_settable, loc_existable, loc_deletable
4. Extend value bases with mutation methods (ListBase.append, DictBase.clear, etc.)

### Phase 4: every_pv — Simplify
1. Update all imports (IntRef → IntValue, IntRefBase → IntBase, etc.)
2. Delete redundant morphisms (mapping.py, sequence.py, set.py → use everybase)
3. Delete redundant traits (use everybase capabilities instead)
4. Delete redundant protocols (use everybase capability protocols)
5. Keep: ref.py, shape.py, spans.py, slots/, PV-specific morphisms, reactive
6. Update PV refs to inherit from everybase capability bases

### Phase 5: every_pv — Tests
1. Update all test imports
2. Verify PV views work with everybase operations
3. Run full test suite

### Phase 6 (future): every_py
1. Create package with PyShape, PyRefBase, DictItemRef, slots
2. Implement Shape-backed Python dict substrate
3. Tests
