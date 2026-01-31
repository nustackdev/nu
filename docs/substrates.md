# Substrates

A substrate is where data actually lives. everyabc defines the computation model, everybase provides reusable building blocks, and substrates wire it all to real storage.

## What a Substrate Provides

1. **Refs** — the navigation layer (how to resolve a reference to a storage location)
2. **Protocol implementations** — make storage objects support standard Python protocols
3. **Spans** — context boundaries (transaction, snapshot, etc.) if the storage needs them
4. **Shapes / Slots** — declarative schemas if the substrate supports structured data

Everything else comes from everybase for free: type algebra, value wrappers, morphisms, capability bases, utilities.


## The Span-Context Model

Spans scope Context for their children. At execution time:

```
Span.enter(ctx)        → child_ctx      # add handles for children
  children.execute(child_ctx)            # children use scoped context
Span.exit_success(ctx) → cleanup        # or exit_failure on error
```

Context is a type-keyed bag of handles with optional **shape discrimination** for multi-store scenarios:

```python
# Singleton handle (one per type)
ctx = Context().with_handle(NotionClient, client)
client = ctx.get(NotionClient)

# Shape-scoped handle (one per type+shape)
ctx = ctx.with_handle(StorageProtocol, user_db, shape=UserShape)
ctx = ctx.with_handle(StorageProtocol, order_db, shape=OrderShape)
user_db = ctx.get(StorageProtocol, shape=UserShape)

# Lazy factory (created on first access)
ctx = ctx.with_factory(TransactionProtocol, lambda: db.begin_txn(), shape=UserShape)
txn = ctx.get(TransactionProtocol, shape=UserShape)  # opens on first call

# Check if lazy handle was actually opened
ctx.was_opened(TransactionProtocol, shape=UserShape)  # True if accessed
```

Each ref knows its shape via `ref.get_root_shape()` and uses it to look up the correct handle.


## Example: PV Substrate (every_pv)

PV (Polymorphic Views) is the primary substrate. Data lives in KV stores (RocksDB, LMDB, etc.) accessed through typed views.

### Handle Lifecycle

```
StorageProtocol (long-lived, app-scoped)
    │
    │  Span.enter() opens:
    ▼
TransactionProtocol / SnapshotProtocol (short-lived, span-scoped)
    │
    │  View.open_root(txn) wraps:
    ▼
View (stateless accessor over storage context)
    │
    │  ctx.get(View, shape=S) consumed by:
    ▼
Term.execute(ctx) → result
```

| Handle | Lifecycle | Purpose |
|--------|-----------|---------|
| `StorageProtocol` | App-scoped | Connection to storage |
| `TransactionProtocol` / `SnapshotProtocol` | Span-scoped | Atomic access |
| `View` | Span-scoped | Typed data navigation |

### PVAtomic Span

The key span for PV operations. Opens a storage transaction lazily and provides a View on top of it.

```python
class PVAtomic(Span):
    """Atomic transaction boundary for PV operations.

    On enter:
      1. Gets StorageProtocol from context (by shape)
      2. Registers lazy factory for TransactionProtocol
      3. Registers lazy factory for View (depends on transaction)

    On exit:
      - Success: commit transaction (if opened)
      - Failure: abort transaction (if opened)

    Lazy: if no child accesses storage, no transaction is opened.
    """

    def __init__(self, shape: type, view_type: type, *children):
        super().__init__(*children)
        self.shape = shape
        self._txn = None

    def enter(self, ctx: Context) -> Context:
        storage = ctx.get(StorageProtocol, shape=self.shape)

        def open_txn():
            self._txn = storage.begin_transaction()
            return self._txn

        def open_view():
            txn = ctx_with_txn.get(TransactionProtocol, shape=self.shape)
            return ViewCls.open_root(txn)

        ctx_with_txn = ctx.with_factory(
            TransactionProtocol, open_txn, shape=self.shape
        )
        return ctx_with_txn.with_factory(
            View, open_view, shape=self.shape
        )

    def exit_success(self, ctx: Context) -> None:
        if self._txn is not None:
            self._txn.commit()

    def exit_failure(self, ctx: Context, error: Exception) -> None:
        if self._txn is not None:
            self._txn.abort()
```

PVAtomic inspects subtree purity: if all terms are Operations (pure), opens a read-only snapshot instead of a transaction. If no child accesses storage at all, nothing is opened.

### PV Shapes and Slots

Declarative schemas for PV data:

```python
class User(PVShape):
    name = StrSlot()
    age = IntSlot()
    tasks = ListSlot(str)
    profile = ShapeSlot(Profile)
```

PVShapeMeta collects Slots at class creation, replaces them with SlotDescriptors. Accessing `User.name` at class level calls `SlotDescriptor.__get__()` which calls `slot.create_ref()` → returns a PVItemRef. Shapes are never instantiated.

### PV Ref Hierarchy

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
    ├── PVDictRef[K, V]        mapping of primitives
    ├── PVListRef[T]           sequence of primitives
    ├── PVShapeRef[S]          nested shape (attr access → child refs)
    ├── PVShapesListRef[S]     list of shapes
    └── PVShapesDictRef[K, S]  dict of shapes
```

Primitive refs mix in everybase type bases (IntType, StrType, ...) to get operator methods. Item refs inherit everybase capability bases (ItemGettableBase, ItemSettableBase, ...) for `.get()`, `.set()`, `.exists()`, `.remove()`, `.on_change()`.

### E2E Flow

```
1. Setup
   ├─ Create storage connections
   ├─ Build initial Context with storages (shape-scoped)
   └─ Build topology tree

2. Execute
   ├─ Executor walks tree
   ├─ PVAtomic.enter(ctx)
   │   ├─ Registers lazy TransactionProtocol factory
   │   └─ Registers lazy View factory
   │   └─ Returns child_ctx
   │
   ├─ Term.execute(child_ctx)
   │   ├─ ctx.get(View, shape=S)  ← triggers View factory
   │   │   └─ View factory calls ctx.get(TransactionProtocol)  ← triggers txn factory
   │   │       └─ txn factory calls storage.begin_transaction()
   │   ├─ Navigates view, reads/writes data
   │   └─ Returns result
   │
   └─ PVAtomic.exit_success(child_ctx)
       └─ txn.commit() (only if txn was opened)

3. Cleanup
   └─ Storage connections closed by application
```

### Usage

```python
class AppState(PVShape):
    name = StrSlot()
    age = IntSlot()

with Storage(".db", codec=Codec()) as storage:
    ctx = Context().with_handle(StorageProtocol, storage, shape=AppState)

    # Write (transaction)
    await PVAtomic(AppState, DictView,
        Seq(
            AppState.name.set("Alice"),
            AppState.age.set(30),
        )
    ).execute(ctx)

    # Read (snapshot — pure subtree)
    await PVAtomic(AppState, DictView,
        Seq(
            Print("name", AppState.name.get()),
            Print("age", AppState.age.get()),
        )
    ).execute(ctx)
```


## Tree Transforms

Spans are structural — they can be added or removed via tree transforms. This enables meta-level operations on context boundaries.

### Atomicize

Automatically wrap subtrees that access storage in atomic boundaries:

```python
def atomicize(tree: Executable, shape: type) -> Executable:
    def wrap_if_needed(node):
        if isinstance(node, Flow):
            refs = find(node, lambda n: (
                isinstance(n, Term)
                and hasattr(n, 'ref')
                and n.ref.get_root_shape() == shape
            ))
            if refs:
                return PVAtomic(shape, node)
        return node
    return map_nodes(tree, wrap_if_needed)
```

### Tracing

Add observability spans:

```python
def add_tracing(tree: Executable) -> Executable:
    def wrap(node):
        if isinstance(node, Term):
            return Traced(repr(node), node)
        return node
    return map_nodes(tree, wrap)
```

### Checkpointing

Add crash recovery spans around flow children:

```python
def add_checkpoints(tree: Executable, state_store) -> Executable:
    def wrap_children(node):
        if isinstance(node, Seq):
            new_children = [
                Checkpoint(state_store, i, child)
                for i, child in enumerate(node.children)
            ]
            return node.with_children(*new_children)
        return node
    return map_nodes(tree, wrap_children)
```


## Multi-Store

Multiple stores are supported via shape-scoped handles:

```python
class UserShape(Shape): ...
class OrderShape(Shape): ...

ctx = (Context()
    .with_handle(StorageProtocol, rocksdb_users, shape=UserShape)
    .with_handle(StorageProtocol, rocksdb_orders, shape=OrderShape)
    .with_handle(NotionClient, notion)  # singleton, no shape
)

tree = Seq(
    PVAtomic(UserShape, DictView,
        user_ref.name.set("Alice"),
    ),
    PVAtomic(OrderShape, DictView,
        order_ref.total.set(price_ref.get()),
    ),
    Notion.Insert(table, user_ref.name.get()),
)
```

Each PVAtomic opens its own transaction on its own store. Refs resolve to the correct store via their shape. Cross-store operations work because Context holds all handles.
