# Context

Context is an immutable, type-keyed bag of handles:

```python
from everybase import Context

# Register handles by type
ctx = Context()
ctx = ctx.with_handle(SolanaRpc, rpc_client)
ctx = ctx.with_handle(dict, data, shape=MyShape)

# Look up by type
rpc = ctx.get(SolanaRpc)
data = ctx.get(dict, shape=MyShape)

# Lazy factories (created on first access)
ctx = ctx.with_factory(SolanaRpc, create_rpc)
rpc = ctx.get(SolanaRpc)  # factory called here, not before

# Check if lazy factory was materialized
ctx.was_opened(SolanaRpc)  # True if accessed
```

Shape discrimination enables multi-store:

```python
ctx = (Context()
    .with_handle(StorageProtocol, user_db, shape=UserShape)
    .with_handle(StorageProtocol, order_db, shape=OrderShape)
)

user_db = ctx.get(StorageProtocol, shape=UserShape)   # different store
order_db = ctx.get(StorageProtocol, shape=OrderShape)  # different store
```

## Example: PVAtomic

The PV substrate's transaction boundary:

```python
from every_pv import Atomic
from every_pv.views import DictView

tree = Atomic(UserShape, DictView,
    Seq(
        UserShape.name.set("Alice"),
        UserShape.age.set(30),
    ),
)
await tree.execute(ctx)
```

What `Atomic` does on enter:

1. Gets `StorageProtocol` from context (by shape)
2. Registers lazy factory for `TransactionProtocol`
3. Registers lazy factory for `View` (depends on transaction)

What it does on exit:

- Success: commit transaction (if opened)
- Failure: abort transaction (if opened)

Smart behavior:

- If subtree is pure (only reads) -> opens read-only snapshot instead
- If no child accesses storage -> nothing is opened at all

## Example: Multi-Store Transaction

```python
from every_pv import Atomic
from every_pv.views import DictView
from every_flow import Seq

tree = Seq(
    # Transaction on user store
    Atomic(UserShape, DictView,
        user.name.set("Alice"),
    ),
    # Separate transaction on order store
    Atomic(OrderShape, DictView,
        order.total.set(price.get()),
    ),
)

ctx = (Context()
    .with_handle(StorageProtocol, user_db, shape=UserShape)
    .with_handle(StorageProtocol, order_db, shape=OrderShape)
)

await tree.execute(ctx)
```

Each `Atomic` opens its own transaction on its own store.

## Example: Auto-Atomicize via Tree Transform

Spans are structural — they can be added/removed via tree transforms:

```python
from everybase.tree import find, map_nodes
from every_pv import Atomic

def atomicize(tree, shape):
    """Wrap subtrees that access storage in atomic boundaries."""
    def wrap_if_needed(node):
        if isinstance(node, Flow):
            refs = find(node, lambda n: (
                isinstance(n, Term)
                and hasattr(n, 'ref')
                and n.ref.get_root_shape() == shape
            ))
            if refs:
                return Atomic(shape, DictView, node)
        return node
    return map_nodes(tree, wrap_if_needed)

# Before: raw tree, no transactions
tree = Seq(User.name.set("Eve"), User.age.set(25))

# After: automatically wrapped
safe_tree = atomicize(tree, User)
```
