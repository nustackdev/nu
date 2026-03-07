# Substrates

A substrate is where data actually lives. It takes abstract types and connects them to real storage.

## What a Substrate Provides

1. **Refs** — the navigation layer (how a reference resolves to a storage location)
2. **Protocol implementations** — make storage objects support standard Python protocols
3. **Spans** — context boundaries (transactions, snapshots) if storage needs them

Everything else comes from everybase for free: type algebra, values, morphisms, capability bases, utilities.

## Available Substrates

### eb-dict (simple, in-memory)

Plain nested Python dicts. No persistence, no reactivity.

```python
from eb_dict import IntRef, StrRef, FloatRef, ListRef, DictRef
from eb_dict import ShapeRef, ShapesListRef, ShapesDictRef
from everybase.shape import Shape
from everybase import Context

class Counter(Shape):
    value = IntRef.slot()
    label = StrRef.slot()

data = {}
ctx = Context().bind(data, dict, Counter)

await Counter.value.set(42).execute(ctx)
await Counter.label.set("clicks").execute(ctx)
print(data)  # {"value": 42, "label": "clicks"}
```

Use when: prototyping, ephemeral state, in-memory counters.

### eb-virtuals (persistent, reactive)

Polymorphic Views over KV stores (RocksDB, LMDB, etc.). Full persistence and reactivity.

```python
from eb_virtuals import IntRef, StrRef, FloatRef, Atomic
from virtuals.views import DictView
from virtuals.codecs import TextCodec as Codec
from eb_virtuals.presetss.textdb import TextStorage as Storage
from everybase.shape import Shape
from everybase import Context

class AppState(Shape):
    name = StrRef.slot()
    age = IntRef.slot()

with Storage(".db", codec=Codec()) as storage:
    ctx = Context().bind(storage, StorageProtocol, AppState)

    # Write (opens transaction)
    await Atomic(
        Seq(
            AppState.name.set("Alice"),
            AppState.age.set(30),
        ),
        scope=AppState,
    ).execute(ctx)

    # Read (opens snapshot — pure subtree)
    await Atomic(
        Print("name", AppState.name.get()),
        scope=AppState,
    ).execute(ctx)
```

Use when: persistent state, reactive subscriptions, transactional consistency.

## From Type to Ref: The Full Path

A custom type becomes usable in shapes through this chain:

```
TypeBase[T]        abstract operations (what you can do)
    |
ValueBase          computed result (Python memory)
    |
ItemRef[T, V]      storage contract (get/set)
    |
    +-- PrimitiveRef (eb-virtuals)     persistent leaf ref
    +-- DictRefBase (eb_dict)    dict leaf ref
```

### Concrete Example: Making a Pubkey Ref

**Step 1: Type + Value** (substrate-agnostic, defined once):

```python
from everybase.abc import EqualableBase, TypeBase, ValueBase, FuncCallOp

class PubkeyType(EqualableBase, TypeBase[Pubkey | Sentinel]):
    @classmethod
    def from_string(cls, s): return PubkeyValue(FuncCallOp(Pubkey.from_string, s))

class PubkeyValue(ValueBase, PubkeyType):
    pass
```

**Step 2: RefBase** (substrate-agnostic, defines get/set):

```python
from everybase.shape import ItemRef
from everybase.shape.morphisms import ItemGetOp, ItemSetCmd

class PubkeyRefBase(ItemRef[Pubkey, PubkeyValue], PubkeyType):
    def get(self) -> PubkeyValue:
        return PubkeyValue.from_string(StrValue(ItemGetOp(self)))

    def set(self, value) -> PubkeyValue:
        return PubkeyValue(ItemSetCmd(self, ensure_term(str(value))))
```

**Step 3: Substrate Refs** (one per substrate):

```python
from eb_virtuals import PrimitiveRef
from eb_dict import RefBase as DictRefBase
from everybase.shape import Slot

class PVPubkeyRef(PubkeyRefBase, PrimitiveRef):
    @classmethod
    def slot(cls):
        return Slot(cls, value_type=str)

class DictPubkeyRef(PubkeyRefBase, DictRefBase):
    @classmethod
    def slot(cls):
        return Slot(cls)
```

**Step 4: Use in shapes:**

```python
class Token(Shape):
    mint = DictPubkeyRef.slot()      # dict substrate
    # or
    mint = PVPubkeyRef.slot()        # PV substrate
```

## Mixed Substrates

Different shapes can use different substrates in the same tree:

```python
from eb_virtuals import StrRef as PVStrRef
from eb_dict import IntRef as MemIntRef

class PersistentData(Shape):
    """Stored on disk."""
    name = PVStrRef.slot()

class EphemeralCounters(Shape):
    """In-memory only."""
    requests = MemIntRef.slot()

# Setup both
data = {}
ctx = Context().bind(data, dict, EphemeralCounters)

with Storage(".db", codec=Codec()) as storage:
    ctx = ctx.bind(storage, StorageProtocol, PersistentData)

    # Both substrates in one tree
    tree = Seq(
        Atomic(
            PersistentData.name.set("Alice"),
            scope=PersistentData,
        ),
        EphemeralCounters.requests.set(
            EphemeralCounters.requests.get() + 1,
        ),
    )
    await tree.execute(ctx)
```

Context routes each ref to the correct store via scope.

## Ref Hierarchy per Substrate

Both substrates provide the same ref types:

| Ref Type | Dict (`eb_dict`) | PV (`eb_virtuals`) |
|----------|-------|------|
| Primitives | `IntRef`, `StrRef`, `FloatRef`, `BoolRef`, `BytesRef` | same names |
| Extended | `DecimalRef`, `DatetimeRef`, `UUIDRef`, `PathRef`, etc. | same names |
| Financial | `PercentageRef`, `BasisPointRef` | same names |
| Collections | `ListRef`, `DictRef`, `SetRef` | `ListRef`, `DictRef`, `SetRef` |
| Shapes | `ShapeRef`, `ShapesListRef`, `ShapesDictRef` | same names |

Import from the substrate you want:

```python
from eb_dict import IntRef, StrRef, ShapesListRef  # in-memory
from eb_virtuals import IntRef, StrRef, ShapesListRef    # persistent
```

## Building a New Substrate

A substrate needs to:

1. **Implement Refs** that know how to resolve to the storage backend
2. **Wire protocols** so storage objects support `__getitem__`, `__setitem__`, `__contains__`
3. **Optionally provide Spans** for transactional access

The ref implements `.slot()` to integrate with the Shape system. All type algebra, morphisms, and capability bases come from everybase.abc — no need to reimplement.

See the [everybase substrates doc](../substrates.md) for the full contract.
