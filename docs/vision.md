# Vision

## Three Layers

```text
everybase.core    contracts — pure abstractions, nothing else
everybase.abc     toolbox   — common bases, morphisms, utilities
every_*           substrates — actual storage implementations
```

**everybase.core** defines the computation model: Term, Ref, Value, Morphism, Shape, Slot, Span, Context. It answers "what CAN exist" without saying how anything works. Top-level `everybase` re-exports everything from `everybase.core`.

**everybase.abc** is not a substrate. It doesn't store anything. It provides reusable building blocks — type bases (IntType, ListType), value wrappers (IntValue, ListValue), capability protocol+base pairs, common morphisms (AddOp, MapOp), and utilities (ensure_term, typed_value). Any substrate can import and compose these instead of reimplementing from scratch.

**Substrates** are where data actually lives:

- `everypv` — polymorphic views over KV stores (RocksDB, etc.)
- `eb_dict` (future) — Python dict as a bag, in-memory
- `eb_notion` (future) — Notion API as storage backend
- `every_sqlite` (future) — SQLite as storage

Each substrate provides its own refs, spans, and capability wiring. Each reuses everybase.abc's type algebra and common morphisms where applicable.


## What everybase.core Owns

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

**The founding trio — Term, Flow, Span:**

- Term — what to compute
- Flow — when / in what order to compute it (temporal ordering, dependencies)
- Span — grouping of a subtree (scoped context: enter → child context, exit → cleanup)

**Tree algebra** — generic operations on any tree of nodes:

- Node[ChildT] with immutable reconstruction (with_children)
- Traversals: preorder, postorder, bfs, leaves, ancestors
- Transforms: compose, map_children, replace, graft, prune
- Queries: find, find_first, count, size, depth

**Structure contracts:**

- Shape — declares named fields with Slots
- Slot — factory that creates a Ref for a field

**Infrastructure:**

- Context / Handle — type-keyed handle container for runtime plumbing

**What everybase.core does NOT own:** any opinion about data models (document, relational, graph). Those are specializations that live in everybase.abc or substrate packages. everybase.core only knows that Terms form trees, Refs point to locations, Values hold data, and Morphisms transform things.


## What everybase.abc Provides

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

IntValue, StrValue, FloatValue, BoolValue, BytesValue, ListValue, DictValue, SetValue, NoneValue, AnyValue. These hold either a literal (`IntValue(42)`) or a source Term (`IntValue(AddOp(...))`). Substrates use these as return types.

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
- `loc_item` — ItemGettable, ItemSettable, ItemExistable, ItemDeletable
- `loc_reactive` — Observable, ChildObservable, DescendantsObservable

**Common morphisms** — pure Python operations any substrate can reuse:

- Operators: AddOp, SubOp, MulOp, EqOp, LtOp, NotOp, ...
- Functions: MapOp, FilterOp, ReduceOp, SortedOp, FindOp, ...
- Conversions: ToIntOp, ToStrOp, ToListOp, ...
- Access: AtOp, SliceOp, LenOp, ContainsOp
- Collection mutations: AppendCmd, InsertCmd, PopCmd, SetItemCmd, DeleteItemCmd, AddCmd, RemoveCmd, ClearCmd

These operate via standard Python protocols. Substrates whose storage objects support Pythonic interfaces reuse these directly.

**Utilities:**

- `ensure_term(value)` — convert Python literals to appropriate Value terms
- `typed_value(type, op)` — wrap a morphism in the correct Value type
- `combiners` — and_, or_, all_, any_, ifelse, coalesce


## Standardized Substrate Contracts

Three patterns are generic — they all follow the same design: everybase.abc defines protocols + morphisms + bases, substrates provide refs (navigation) and protocol implementations on their storage objects.

### Item Access

A ref has a parent (the collection) and an address (key/index). Operations use standard Python protocols on the parent.

```python
ItemGetOp(ref)        →  parent[address]           # __getitem__
ItemSetCmd(ref, val)  →  parent[address] = val     # __setitem__
ItemDeleteCmd(ref)    →  del parent[address]       # __delitem__
ItemExistsOp(ref)     →  address in parent         # __contains__
```

The substrate-specific part is entirely in the **ref** — how the parent navigates to the collection. The morphisms don't care.

Capability bases wire these to methods:

- `ItemGettableBase` → `.get()` wrapping ItemGetOp
- `ItemSettableBase` → `.set(value)` wrapping ItemSetCmd
- `ItemDeletableBase` → `.remove()` wrapping ItemDeleteCmd
- `ItemExistableBase` → `.exists()`, `.missing()`

### Extract / Store

"Get entire collection as a Python value" and "replace entire collection from a Python value." Standardized as two protocols:

- **Convertible** — `.extract() → dict | list | set | ...`
- **Initializable** — `.store(data)` — replace contents from Python value

### Reactivity

Change observation at various granularities. Substrate storage objects implement observable protocols, everybase.abc provides the morphisms and bases.

- **Observable** — `.on_change() → Subscription`
- **ChildObservable** — `.on_child_change(key) → Subscription`
- **ChildrenObservable** — `.on_children_change() → Subscription`
- **DescendantsObservable** — `.on_descendants_change(pattern) → Subscription`

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
