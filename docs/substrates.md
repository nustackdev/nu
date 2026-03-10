# Substrates

A substrate is where data actually lives. everybase defines the computation model (via everybase.core) and provides reusable building blocks (via everybase.abc), and substrates wire it all to real storage.

## What a Substrate Provides

1. **Refs** -- the navigation layer (how to resolve a reference to a storage location)
   - Each Ref class implements `.slot()` classmethod with typed signature for IDE autocomplete
2. **Protocol implementations** -- make storage objects support standard Python protocols
3. **Spans** -- context boundaries (transaction, snapshot, etc.) if the storage needs them

Everything else comes from everybase for free: type algebra, value wrappers, morphisms, capability bases, Slot, Ref (document-model base), utilities. The `Slot` abstraction is an internal implementation detail -- users just use `Ref.slot()`.


## The Span-Context Model

Spans scope Context for their children. At execution time:

```
Span.enter(ctx)        -> child_ctx      # add handles for children
  children.execute(child_ctx)            # children use scoped context
Span.exit_success(ctx) -> cleanup        # or exit_failure on error
```

Context is a type-keyed bag of handles with optional **scope discrimination** for multi-store scenarios:

```python
# Singleton handle (one per type)
ctx = Context().bind(client, NotionClient)
client = ctx[NotionClient]

# Scope-discriminated handle (one per type+scope)
ctx = ctx.bind(user_db, StorageProtocol, UserShape)
ctx = ctx.bind(order_db, StorageProtocol, OrderShape)
user_db = ctx[StorageProtocol, UserShape]

# Lazy factory (created on first access)
ctx = ctx.lazy(lambda: db.begin_txn(), TransactionProtocol, UserShape)
txn = ctx[TransactionProtocol, UserShape]  # opens on first call

# Check if lazy handle was actually opened
ctx.was_opened(TransactionProtocol, scope=UserShape)  # True if accessed
```

Each ref knows its scope via `ref.get_root_shape()` and uses it to look up the correct handle.


## Example: PV Substrate (eb-virtuals)

PV (Polymorphic Views) is the primary substrate. Data lives in KV stores (RocksDB, LMDB, etc.) accessed through typed views.

### Lifecycle

```
StorageProtocol (long-lived, app-scoped)
    |
    |  Span.enter() opens:
    v
TransactionProtocol / SnapshotProtocol (short-lived, span-scoped)
    |
    |  View.open_root(txn) wraps:
    v
View (stateless accessor over storage context)
    |
    |  ctx[View, S] consumed by:
    v
Term.execute(ctx) -> result
```

| Type | Lifecycle | Purpose |
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
      1. Gets StorageProtocol from context (by scope)
      2. Registers lazy factory for TransactionProtocol
      3. Registers lazy factory for View (depends on transaction)

    On exit:
      - Success: commit transaction (if opened)
      - Failure: abort transaction (if opened)

    Lazy: if no child accesses storage, no transaction is opened.
    """

    def __init__(self, *children, scope=None, view_cls=DictView):
        super().__init__(*children)
        self.scope = scope
        self.view_cls = view_cls
        self._txn = None

    def enter(self, ctx: Context) -> Context:
        storage = ctx[StorageProtocol, self.scope]

        def open_txn():
            self._txn = storage.begin_transaction()
            return self._txn

        def open_view():
            txn = ctx_with_txn[TransactionProtocol, self.scope]
            return self.view_cls.open_root(txn)

        ctx_with_txn = ctx.lazy(open_txn, TransactionProtocol, self.scope)
        return ctx_with_txn.lazy(open_view, View, self.scope)

    def exit_success(self, ctx: Context) -> None:
        if self._txn is not None:
            self._txn.commit()

    def exit_failure(self, ctx: Context, error: Exception) -> None:
        if self._txn is not None:
            self._txn.abort()
```

PVAtomic inspects subtree purity: if all terms are Operations (pure), opens a read-only snapshot instead of a transaction. If no child accesses storage at all, nothing is opened.

### PV Shapes

Declarative schemas for PV data using `Ref.slot()`:

```python
class User(Shape):
    name = StrRef.slot()
    age = IntRef.slot()
    tasks = ListRef.slot(str)
    profile = ShapeRef.slot(Profile)
```

ShapeMeta collects Slots at class creation, replaces them with SlotDescriptors. Accessing `User.name` at class level calls `SlotDescriptor.__get__()` which calls `slot.create_ref()` -> returns the appropriate Ref. Shapes are never instantiated.

### PV Ref Hierarchy

```text
PVRefBase[T]                    address + parent chain + shape association
├── PVPrimitiveRef[T]           leaf values -- resolve() -> path, fetch() -> view[key]
│   ├── PVIntRef                = PVPrimitiveRef[int] + IntType
│   ├── PVStrRef                = PVPrimitiveRef[str] + StrType
│   ├── PVFloatRef, PVBoolRef, PVBytesRef
│   ├── PVItemRef[T, VT]       standalone item in a shape
│   ├── PVListItemRef[T, VT]   item within a list
│   └── PVDictItemRef[T, VT]   item within a dict
│
└── PVViewRef[T, ViewT]        container views -- resolve() -> path, fetch() -> View
    ├── PVDictRef[K, V]        mapping of primitives
    ├── PVListRef[T]           sequence of primitives
    ├── PVShapeRef[S]          nested shape (attr access -> child refs)
    ├── PVShapesListRef[S]     list of shapes
    └── PVShapesDictRef[K, S]  dict of shapes
```

Primitive refs mix in everybase.abc type bases (IntType, StrType, ...) to get operator methods. Item refs inherit everybase.abc capability bases (ItemSettableBase, ItemDeletableBase, ...) for `.store()`, `.erase()`, `.exists()`, `.on_change()`. Refs are terms — executing a ref reads its value directly (no separate `.load()` needed).

### E2E Flow

```
1. Setup
   ├─ Create storage connections
   ├─ Build initial Context with storages (scope-keyed)
   └─ Build topology tree

2. Execute
   ├─ Executor walks tree
   ├─ PVAtomic.enter(ctx)
   │   ├─ Registers lazy TransactionProtocol factory
   │   └─ Registers lazy View factory
   │   └─ Returns child_ctx
   │
   ├─ Term.execute(child_ctx)
   │   ├─ ctx[View, S]  <- triggers View factory
   │   │   └─ View factory calls ctx[TransactionProtocol]  <- triggers txn factory
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
class AppState(Shape):
    name = StrRef.slot()
    age = IntRef.slot()

with Storage(".db", codec=Codec()) as storage:
    ctx = Context().bind(storage, StorageProtocol, AppState)

    # Write (transaction)
    await PVAtomic(
        Seq(
            AppState.name.set("Alice"),
            AppState.age.set(30),
        ),
        scope=AppState,
    ).execute(ctx)

    # Read (snapshot -- pure subtree)
    await PVAtomic(
        Seq(
            Print("name", AppState.name.get()),
            Print("age", AppState.age.get()),
        ),
        scope=AppState,
    ).execute(ctx)
```


## Tree Transforms

Spans are structural -- they can be added or removed via tree transforms. This enables meta-level operations on context boundaries.

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
                return PVAtomic(node, scope=shape)
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

Multiple stores are supported via scope-discriminated handles:

```python
class UserShape(Shape): ...
class OrderShape(Shape): ...

ctx = (Context()
    .bind(rocksdb_users, StorageProtocol, UserShape)
    .bind(rocksdb_orders, StorageProtocol, OrderShape)
    .bind(notion, NotionClient)  # singleton, no scope
)

tree = Seq(
    PVAtomic(
        user_ref.name.set("Alice"),
        scope=UserShape,
    ),
    PVAtomic(
        order_ref.total.set(price_ref.get()),
        scope=OrderShape,
    ),
    Notion.Insert(table, user_ref.name.get()),
)
```

Each PVAtomic opens its own transaction on its own store. Refs resolve to the correct store via their scope. Cross-store operations work because Context holds all handles.
