# Span-Context: How Spans Provide Context to Terms

## Overview

Spans are structural grouping nodes in the tree. At execution time, they
scope and shape **Context** for their children. This document describes
the complete model for how resources flow from storage through spans
into terms.

## Specific Example

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

**Three handle types, from three packages:**

| Handle | Package | Lifecycle | Purpose |
|--------|---------|-----------|---------|
| `StorageProtocol` | tkv | App-scoped | Connection to storage |
| `TransactionProtocol` / `SnapshotProtocol` | tkv | Span-scoped | Atomic access |
| `View` | pv | Span-scoped | Typed data navigation |

## Context

Context is a type-keyed bag of handles with optional **shape discrimination**
for multi-store scenarios.

```python
from everyabc import Context

# Singleton handle (one per type)
ctx = Context().with_handle(NotionClient, client)
client = ctx.get(NotionClient)

# Shape-scoped handle (one per type+shape)
ctx = ctx.with_handle(StorageProtocol, user_db, shape=UserShape)
ctx = ctx.with_handle(StorageProtocol, order_db, shape=OrderShape)
user_db = ctx.get(StorageProtocol, shape=UserShape)

# Lazy factory (created on first access)
ctx = ctx.with_factory(TransactionProtocol, lambda: db.begin_transaction(), shape=UserShape)
txn = ctx.get(TransactionProtocol, shape=UserShape)  # opens on first call

# Check if lazy handle was actually opened
ctx.was_opened(TransactionProtocol, shape=UserShape)  # True if accessed
```

Shape discrimination replaces the old `get_context_for_shape()` dispatch.
Each ref knows its shape via `ref.get_root_shape()` and uses it to look up
the correct handle.

## Executor

The executor traverses the tree and dispatches by node type:

```python
def execute(node: Exec, ctx: Context) -> Any:
    if isinstance(node, Span):
        child_ctx = node.enter(ctx)         # span scopes context
        try:
            results = [execute(c, child_ctx) for c in node.children]
            result = results[-1] if results else None
            node.exit_success(child_ctx)     # cleanup on success
            return result
        except Exception as e:
            node.exit_failure(child_ctx, e)  # cleanup on failure
            raise

    elif isinstance(node, Flow):
        return node.execute_flow(ctx, lambda c: execute(c, ctx))

    elif isinstance(node, Term):
        return node.execute(ctx)             # term does work
```

**Key rules:**
- Span: `enter()` → run children → `exit_success/exit_failure()`
- Flow: controls child execution order (seq, par, cond)
- Term: evaluates, can call `child.execute(ctx)` for nested terms

## Spans as Context Shapers

### Span Protocol

Spans optionally implement `enter()` / `exit_success()` / `exit_failure()`
to scope context for their children:

```python
class MySpan(Span):
    def enter(self, ctx: Context) -> Context:
        """Add/modify handles for children. Return new context."""
        return ctx

    def exit_success(self, ctx: Context) -> None:
        """Cleanup on successful execution."""
        pass

    def exit_failure(self, ctx: Context, error: Exception) -> None:
        """Cleanup on failure."""
        pass
```

Spans without these methods are transparent (pass-through).

### PVAtomic Span

The key span for PV operations. Opens a storage transaction/snapshot
lazily and provides a View on top of it.

```python
from tkv.tkv.storage import StorageProtocol, TransactionProtocol, SnapshotProtocol
from pv.view import View

class PVAtomic(Span):
    """Atomic transaction boundary for PV operations.

    On enter:
      1. Gets StorageProtocol from context (by shape)
      2. Registers lazy factory for TransactionProtocol
      3. Registers lazy factory for View (depends on transaction)

    On exit:
      - Success: commit transaction (if opened)
      - Failure: abort transaction (if opened)

    Lazy: if children only read and a snapshot suffices,
    or if no child accesses storage at all, no transaction is opened.
    """

    def __init__(self, shape: type, *children):
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

### PVSnapshot Span

Read-only variant for pure subtrees:

```python
class PVSnapshot(Span):
    """Read-only snapshot boundary for PV operations."""

    def __init__(self, shape: type, *children):
        super().__init__(*children)
        self.shape = shape
        self._snap = None

    def enter(self, ctx: Context) -> Context:
        storage = ctx.get(StorageProtocol, shape=self.shape)

        def open_snap():
            self._snap = storage.begin_snapshot()
            return self._snap

        def open_view():
            snap = new_ctx.get(SnapshotProtocol, shape=self.shape)
            return ViewCls.open_root(snap)

        new_ctx = ctx.with_factory(
            SnapshotProtocol, open_snap, shape=self.shape
        )
        return new_ctx.with_factory(
            View, open_view, shape=self.shape
        )

    def exit_success(self, ctx: Context) -> None:
        if self._snap is not None:
            self._snap.close()

    def exit_failure(self, ctx: Context, error: Exception) -> None:
        if self._snap is not None:
            self._snap.close()
```

## Terms Consuming Context

Terms get the exact context they need via typed lookup.
No `get_context_for_shape()` dispatch. Each ref knows its shape.

```python
class GetOp(Term):
    def __init__(self, ref: PVPrimitiveRef):
        self.ref = ref

    def execute(self, ctx: Context):
        shape = self.ref.get_root_shape()
        view = ctx.get(View, shape=shape)       # gets correct view
        path = self.ref.resolve(ctx)
        parent_view, key = navigate(view, path)
        return parent_view[key]

class SetCmd(Term):
    def __init__(self, ref: PVPrimitiveRef, value: Term):
        super().__init__(value)
        self.ref = ref

    def execute(self, ctx: Context):
        shape = self.ref.get_root_shape()
        view = ctx.get(View, shape=shape)       # same view, backed by txn
        value = self.children[0].execute(ctx)   # evaluate child term
        path = self.ref.resolve(ctx)
        parent_view, key = navigate(view, path)
        parent_view[key] = value
        return value
```

### Nested Term Evaluation

Terms evaluate their own children. Context flows down unchanged
unless a span reshapes it.

```python
# Tree: Set(ref, Add(Get(ref_a), Get(ref_b)))
#
# Evaluation:
#   SetCmd.execute(ctx)
#     └─ Add.execute(ctx)
#          ├─ GetOp.execute(ctx) → value_a
#          └─ GetOp.execute(ctx) → value_b
#          return value_a + value_b
#     view[key] = result
```

Cross-store operations work because context holds all handles:

```python
# Notion.Insert(table, PV.Get(ref))
#
# InsertCmd.execute(ctx)
#   └─ PVGetOp.execute(ctx) → data    # uses ctx.get(View, shape=PVShape)
#   notion = ctx.get(NotionClient)      # uses ctx.get(NotionClient)
#   notion.insert(table, data)
```

## Lazy Context Creation

Handles are created on-demand via factories:

```
with_factory(T, fn, shape=S)  →  registers factory
ctx.get(T, shape=S)           →  calls fn() on first access, caches result
ctx.was_opened(T, shape=S)    →  True if factory was called
```

This matters for:
1. **Atomic span**: transaction not opened if children don't access storage
2. **Snapshot span**: snapshot not opened if children don't read
3. **Resource efficiency**: connections opened only when needed

## Auto-Select: Snapshot vs Transaction

`PVAtomic` can inspect subtree purity to auto-select context type:

```python
from everyabc import find

class PVAtomic(Span):
    def enter(self, ctx):
        storage = ctx.get(StorageProtocol, shape=self.shape)

        # Check if subtree is pure (all terms are read-only)
        has_impure = any(
            not t.is_pure
            for t in find(self, lambda n: isinstance(n, Term))
        )

        if has_impure:
            # Impure subtree → transaction
            def open():
                self._txn = storage.begin_transaction()
                return self._txn
            return ctx.with_factory(TransactionProtocol, open, shape=self.shape)
        else:
            # Pure subtree → snapshot (cheaper)
            def open():
                self._snap = storage.begin_snapshot()
                return self._snap
            return ctx.with_factory(SnapshotProtocol, open, shape=self.shape)
```

## Tree Transforms for Context

Spans are structural — they can be added/removed via tree transforms.
This enables meta-level operations on context boundaries.

### Atomicize Transform

Automatically wrap subtrees that access storage in atomic boundaries:

```python
from everyabc import map_nodes, find

def atomicize(tree: Exec, shape: type) -> Exec:
    """Wrap subtrees touching storage in PVAtomic spans.

    Finds nodes that access storage (via refs with matching shape)
    and wraps them in atomic boundaries.
    """
    def wrap_if_needed(node):
        if isinstance(node, Flow):
            # Check if any child term touches this shape's storage
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

### Resumability Transform

Add checkpointing spans around flow nodes for crash recovery:

```python
def add_checkpoints(tree: Exec, state_store) -> Exec:
    """Wrap flow children with checkpoint spans.

    Each child gets wrapped in a Checkpoint span that saves/restores
    execution state. On resume, completed children are skipped.
    """
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

### Tracing Transform

Add observability spans:

```python
def add_tracing(tree: Exec) -> Exec:
    """Wrap all terms in tracing spans for observability."""
    def wrap(node):
        if isinstance(node, Term):
            return Traced(repr(node), node)
        return node

    return map_nodes(tree, wrap)
```

## Multi-Store: Shape as Discriminator

Multiple stores are supported via shape-scoped handles:

```python
class UserShape(Shape): pass
class OrderShape(Shape): pass

# Initial context with multiple stores
ctx = (Context()
    .with_handle(StorageProtocol, rocksdb_users, shape=UserShape)
    .with_handle(StorageProtocol, rocksdb_orders, shape=OrderShape)
    .with_handle(NotionClient, notion)  # singleton, no shape
)

# Tree with spans scoping each store
tree = Seq(
    PVAtomic(UserShape,
        PV.Set(user_ref.name, Lit("Alice"))
    ),
    PVAtomic(OrderShape,
        PV.Set(order_ref.total, PV.Get(price_ref))
    ),
    Notion.Insert(table, PV.Get(user_ref.name))
)
```

Each `PVAtomic` opens its own transaction on its own store.
Refs resolve to the correct store via their shape.

## E2E Flow

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

## Summary

- **Context**: type-keyed bag, shape-scoped, lazy factories
- **Span**: scopes context via enter/exit lifecycle
- **PVAtomic/PVSnapshot**: concrete spans from every_pv, open txn/snap lazily
- **Term**: consumes context via `ctx.get(View, shape=self.ref.shape)`
- **Tree transforms**: atomicize, checkpoint, trace — add spans structurally
- **No PVContext subclass needed**: base Context + tkv protocols + pv View
