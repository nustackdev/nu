# Final Vision: Layer Stack

## 1. Three Layers

```text
everyabc          contracts — pure abstractions, nothing else
everybase         toolbox   — common bases, morphisms, utilities that make building substrates easier
every_*           substrates — actual storage implementations (every_pv, every_dict, every_notion, ...)
```

**everyabc** defines the computation model: Term, Ref, Value, Morphism, Shape, Slot, Span, Context. It answers "what CAN exist" without saying how anything works.

**everybase** is NOT a substrate. It doesn't store anything. It provides reusable building blocks — type bases (IntType, ListType), value wrappers (IntValue, ListValue), capability protocol+base pairs, common morphisms (AddOp, MapOp), and utilities (ensure_term, typed_value). Any substrate can import and compose these instead of reimplementing from scratch.

**Substrates** are where data actually lives:

- `every_pv` — polymorphic views over KV stores (RocksDB, etc.)
- `every_dict` (future) — Python dict as a bag, in-memory
- `every_notion` (future) — Notion API as storage backend
- `every_sqlite` (future) — SQLite as storage

Each substrate provides its own refs, morphisms, and capability wiring. Each reuses everybase's type algebra and common morphisms where applicable.


## 2. What everyabc Owns

The computation model and nothing else.

**Term hierarchy** — the node types that can exist in an expression tree:

```text
Term[T]                     executable node
├── LValue[T]               addressable location (can be target of writes)
│   └── Ref[T]              typed reference — resolve() → address, fetch() → value
└── RValue[T]               evaluable expression (pure, no address)
    ├── Value[T]            typed value holder — literal or wrapping a source Term
    └── Morphism[T]         transformation node
        ├── Operation       pure (deterministic, no side effects)
        └── Command         impure (stateful, order-dependent)
```

**Tree algebra** — generic operations on any tree of nodes:

- Node[ChildT] with immutable reconstruction (with_children)
- Traversals: preorder, postorder, bfs, leaves, ancestors
- Transforms: compose, map_children, replace, graft, prune
- Queries: find, find_first, count, size, depth

**The founding trio — Term, Flow, Span:**

- Term — what to compute
- Flow — when/in what order to compute it (temporal ordering, dependencies)
- Span — grouping of a subtree (e.g. scoped context: enter → child context, exit → cleanup)

**Structure contracts:**

- Shape — declares named fields with Slots
- Slot — factory that creates a Ref for a field

**Infrastructure:**

- Tree algebra — Node construction/reconstruction, traversals (preorder, postorder, bfs), transforms (map, replace, graft, prune), queries (find, count, depth)
- Context / Handle — runtime plumbing for execution

**What everyabc does NOT own:** any opinion about data models (document, relational, graph). Those are specializations that live in everybase or substrate packages. everyabc only knows that Terms form trees, Refs point to locations, Values hold data, and Morphisms transform things.


## 3. What everybase Provides

A toolbox. Everything here exists to save substrates from reimplementing common patterns.

**Type bases** — capability interfaces that substrates mix in:

| Type base | Capabilities mixed in |
|-----------|----------------------|
| IntType | Comparable, Logical, Bitwise, Numeric |
| FloatType | Comparable, Numeric |
| StrType | Comparable, string methods (upper, split, find, ...) |
| BoolType | Comparable, Logical |
| BytesType | Comparable, bytes methods (decode, hex, ...) |
| ListType | MutableSequence, Clearable, Comparable |
| DictType | MutableMapping, Clearable |
| SetType | MutableSet, Clearable |

A substrate ref like `PVIntRef` inherits `IntType` to get arithmetic/comparison/bitwise for free. The type base defines WHAT operations the type supports. The substrate decides HOW they execute.

**Value wrappers** — typed containers for Python literals or computed results:

IntValue, StrValue, FloatValue, BoolValue, BytesValue, ListValue, DictValue, SetValue, NoneValue, AnyValue. These hold either a literal (`IntValue(42)`) or a source Term (`IntValue(AddOp(...))`). Substrates use these as return types — when `PVIntRef.get()` is called, it returns `IntValue(GetOp(ref))`.

**Capability protocol+base pairs** — reusable building blocks for operations:

Each capability is a Protocol (structural contract) paired with a Base (mixin implementation). Organized by domain:

- `gen_arithmetic` — Addable, Subtractable, Negatable, Multiplicative, Numeric
- `gen_comparison` — Orderable, Equalable, Comparable
- `gen_logical` — Andable, Orable, Notable, Logical
- `gen_bitwise` — BitwiseAnd, BitwiseOr, Xor, Shift, Bitwise
- `col_sequence` — Sequence, MutableSequence
- `col_mapping` — Mapping, MutableMapping
- `col_set` — SetLike, MutableSet
- `col_atoms` — Containable, Lengthable, Indexable, Sliceable
- `loc` — LocationGettable, LocationSettable, LocationExistable, LocationDeletable, LocationObservable

The `gen_*` and `col_*` capabilities have both Protocol and Base. Substrates inherit the Bases to get method implementations wired to morphisms.

The `loc_*` capabilities currently have protocols only. Section 5 covers the plan to add morphisms and bases for item access, extract/store, and reactivity — these are standardizable since they operate via Python protocols on whatever object the substrate ref navigates to.

**Common morphisms** — pure Python operations any substrate can reuse:

- Operators: AddOp, SubOp, MulOp, EqOp, LtOp, NotOp, ...
- Functions: MapOp, FilterOp, ReduceOp, SortedOp, FindOp, ...
- Conversions: ToIntOp, ToStrOp, ToListOp, ...
- Access: AtOp, SliceOp, LenOp, ContainsOp
- Collection mutations: AppendCmd, InsertCmd, PopCmd, SetItemCmd, DeleteItemCmd, AddCmd, RemoveCmd, ClearCmd

These operate via standard Python protocols. Substrates whose storage objects support Pythonic interfaces (PV views do, Python dicts do) reuse these directly.

**Utilities:**

- `ensure_term(value)` — convert Python literals to appropriate Value terms
- `typed_value(type, op)` — wrap a morphism in the correct Value type
- `combiners` — and_, or_, all_, any_, ifelse, coalesce

**Document model (loose, not locked in):**

everybase currently provides collection capability bases (MutableSequence, MutableMapping) that implicitly assume a document-like data model (nested dicts/lists). This is intentional but kept loose — it's not promoted to everyabc as a formal contract. Future substrates like every_notion or every_sqlite may need relational shapes, which could be built on top of the document model or as a parallel specialization. The decision to formalize a document model contract in everyabc will come later.


## 4. What every_pv Provides

The PV storage substrate. Data lives in polymorphic views over KV stores (RocksDB, LMDB, etc. via tkv).

**Refs** — real LValues that navigate view hierarchies:

```text
PVRefBase[T]                    address + parent chain + shape association
├── PVPrimitiveRef[T]           leaf values — resolve() → path, fetch() → view[key]
│   ├── PVIntRef                = PVPrimitiveRef[int] + IntType
│   ├── PVStrRef                = PVPrimitiveRef[str] + StrType
│   ├── PVFloatRef, PVBoolRef, PVBytesRef
│   ├── PVItemRef[T, VT]       standalone item in a shape
│   ├── PVListItemRef[T, VT]   item within a list
│   └── PVDictItemRef[T, VT]   item within a dict
│
└── PVViewRef[T, ViewT]        container views — resolve() → path, fetch() → View
    ├── PVDictRef[K, V, ...]   mapping of primitives
    ├── PVListRef[T, ...]      sequence of primitives
    ├── PVShapeRef[S]          nested shape (attr access → child refs)
    ├── PVShapesListRef[S]     list of shapes
    └── PVShapesDictRef[K, S, ...]  dict of shapes
```

Primitive refs mix in everybase type bases (IntType, StrType, ...) to get operator methods.
Collection refs compose PV-specific capability bases into combined ref bases (MutableSequenceRefBase, MutableMappingRefBase).

**Morphisms — what's PV-specific vs what's reusable:**

PV views support Pythonic collection interfaces — `view[key]`, `view.append(x)`, `iter(view)`, `len(view)`, `view.keys()`, etc. This means everybase's collection morphisms (AppendCmd, SetItemCmd, KeysOp, MapOp, FilterOp, ...) work on PV views directly. No need to reimplement them.

What's not in everybase yet (but will be — see section 5):

1. **Collection item semantics** — get/set/delete/exists on an item by address within a collection. Standard Python protocols, not substrate-specific.

2. **Extract/store** — read entire collection as Python value, replace entire collection from Python value. Standardizable as Convertible/Initializable protocols.

3. **Reactive** — change observation at various granularities. Standardizable as Observable protocols + Subscription contract.

**Bases** — wire morphisms to method interfaces:

For collection operations (append, keys, filter, ...), everybase's capability bases are reused since the morphisms work on any Pythonic collection. Item access, extract/store, and reactive bases will also move to everybase once the standardized protocols are in place (section 5).

**Shapes and Slots** — declarative PV schemas:

```python
class User(PVShape):
    name = StrSlot()
    age = IntSlot()
    tasks = ListSlot(str)
    profile = ShapeSlot(Profile)
```

PVShapeMeta collects Slots at class creation, replaces them with SlotDescriptors. Accessing `User.name` calls `SlotDescriptor.__get__()` which calls `slot.create_ref()` → returns a PVItemRef. Shapes are never instantiated — all access is class-level.

**Spans** — transaction/snapshot boundaries:

```python
PVAtomic(User, DictView,
    Seq(
        User.name.set("Alice"),
        User.age.set(30),
    )
).execute(ctx)
```

PVAtomic inspects subtree purity: if all terms are Operations (pure), opens a read-only snapshot instead of a transaction. Lazy — if no child actually accesses storage, nothing is opened. PVSnapshot always opens a snapshot (explicit read-only).


## 5. Standardized Substrate Contracts → everybase

Three patterns currently implemented only in every_pv are actually generic. They all follow the same design: everybase defines protocols + morphisms + bases, substrates provide refs (navigation) and protocol implementations on their storage objects. All in everybase, not everyabc — too early to lock in.

### 5a. Collection Item Access

A ref has a parent (the collection) and an address (key/index). Operations use standard Python protocols on the parent.

```python
# Morphisms — operate via standard Python protocols
ItemGetOp(ref)        →  parent.execute(ctx)[address]           # __getitem__
ItemSetCmd(ref, val)  →  parent.execute(ctx)[address] = val     # __setitem__
ItemDeleteCmd(ref)    →  del parent.execute(ctx)[address]       # __delitem__
ItemExistsOp(ref)     →  address in parent.execute(ctx)         # __contains__
ItemMissingOp(ref)    →  address not in parent.execute(ctx)
```

The substrate-specific part is entirely in the **ref** — how `parent.execute(ctx)` navigates to the collection. PV navigates a view tree. every_dict looks up a Python dict. The morphisms don't care.

Capability bases wire these to methods:

- `ItemGettableBase` → `.get()` wrapping ItemGetOp
- `ItemSettableBase` → `.set(value)` wrapping ItemSetCmd
- `ItemDeletableBase` → `.remove()` wrapping ItemDeleteCmd
- `ItemExistableBase` → `.exists()`, `.missing()`

### 5b. Extract / Store

"Get entire collection as a Python value" and "replace entire collection from a Python value." Standardized as two protocols that storage objects implement:

- **Convertible** — `.extract() → dict | list | set | ...` — serialize collection to Python value
- **Initializable** — `.store(data)` — replace collection contents from Python value

```python
# Morphisms
ExtractOp(ref)          →  ref.execute(ctx).extract()           # Convertible
StoreCmd(ref, data)     →  ref.execute(ctx).store(data)         # Initializable
```

Capability bases:

- `ExtractableBase` → `.get()` for collections, wrapping ExtractOp
- `StorableBase` → `.store(data)` wrapping StoreCmd

PV views already implement Convertible/Initializable. A reactive Python dict can too. Any substrate can.

### 5c. Reactivity

Change observation at various granularities. Substrate storage objects implement observable protocols, everybase provides the morphisms and bases.

**Subscription protocol** — the handle returned by any observation:

```python
class Subscription(Protocol):
    def bind(self, callback: Callable) -> None: ...
    def close(self) -> None: ...
```

**Observable protocols** at different granularities:

- **Observable** — `.on_change() → Subscription` — watch this location for any change
- **ChildObservable** — `.on_child_change(key) → Subscription` — watch a specific child
- **ChildrenObservable** — `.on_children_change() → Subscription` — watch all immediate children
- **DescendantsObservable** — `.on_descendants_change(pattern) → Subscription` — watch subtree

```python
# Morphisms — generic, work with any observable storage object
OnChangeOp(ref)                  →  ref.execute(ctx).on_change()
OnChildChangeOp(ref, key)        →  ref.execute(ctx).on_child_change(key)
OnChildrenChangeOp(ref)          →  ref.execute(ctx).on_children_change()
OnDescendantsChangeOp(ref, pat)  →  ref.execute(ctx).on_descendants_change(pat)
```

Capability bases:

- `ObservableBase` → `.on_change()` wrapping OnChangeOp
- `ChildObservableBase` → `.on_child_change(key)` wrapping OnChildChangeOp
- `ChildrenObservableBase` → `.on_children_change()`
- `DescendantsObservableBase` → `.on_descendants_change(pattern)`

PV views implement these via tkv observers. A reactive Python dict can implement Observable by firing callbacks on `__setitem__`. every_notion can poll and diff. The contract is the same — the implementation varies per substrate.

### Effect on Substrates

With all three patterns standardized, a substrate becomes very thin:

**What a substrate provides:**

1. **Refs** — the navigation layer (how to get from a ref to the storage object)
2. **Protocol implementations** — make storage objects Convertible, Initializable, Observable, etc.
3. **Spans** — transaction/snapshot boundaries (if applicable)
4. **Shapes / Slots** — declarative schemas (if applicable)

**What a substrate gets for free from everybase:**

- Type algebra (IntType, ListType, ...)
- Value wrappers (IntValue, ListValue, ...)
- All collection morphisms (append, keys, filter, map, ...)
- Item access morphisms (get, set, delete, exists)
- Extract/store morphisms
- Reactive morphisms
- All capability bases wiring the above to methods
- Utilities (ensure_term, typed_value, combiners)
