# Context

Context is an immutable, type-keyed bag of handles:

```python
from everybase import Context

# Register handles by type
ctx = Context()
ctx = ctx.bind(rpc_client, SolanaRpc)
ctx = ctx.bind(data, dict, MyShape)

# Look up by type
rpc = ctx[SolanaRpc]
data = ctx[dict, MyShape]

# Lazy factories (created on first access)
ctx = ctx.lazy(create_rpc, SolanaRpc)
rpc = ctx[SolanaRpc]  # factory called here, not before

# Check if lazy factory was materialized
ctx.was_opened(SolanaRpc)  # True if accessed
```

Scope discrimination enables multi-store:

```python
ctx = (Context()
    .bind(user_db, StorageProtocol, UserShape)
    .bind(order_db, StorageProtocol, OrderShape)
)

user_db = ctx[StorageProtocol, UserShape]   # different store
order_db = ctx[StorageProtocol, OrderShape]  # different store
```

## Example: PVAtomic

The PV substrate's transaction boundary:

```python
from everypv import Atomic
from everypv.views import DictView

tree = Atomic(
    Seq(
        UserShape.name.set("Alice"),
        UserShape.age.set(30),
    ),
    scope=UserShape,
)
await tree.execute(ctx)
```

What `Atomic` does on enter:

1. Gets `StorageProtocol` from context (by scope)
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
from everypv import Atomic
from everypv.views import DictView
from everybase.abc import Seq

tree = Seq(
    # Transaction on user store
    Atomic(
        user.name.set("Alice"),
        scope=UserShape,
    ),
    # Separate transaction on order store
    Atomic(
        order.total.set(price.get()),
        scope=OrderShape,
    ),
)

ctx = (Context()
    .bind(user_db, StorageProtocol, UserShape)
    .bind(order_db, StorageProtocol, OrderShape)
)

await tree.execute(ctx)
```

Each `Atomic` opens its own transaction on its own store.

## Example: Auto-Atomicize via Tree Transform

Spans are structural — they can be added/removed via tree transforms:

```python
from everybase.tree import find, map_nodes
from everypv import Atomic

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
                return Atomic(node, scope=shape)
        return node
    return map_nodes(tree, wrap_if_needed)

# Before: raw tree, no transactions
tree = Seq(User.name.set("Eve"), User.age.set(25))

# After: automatically wrapped
safe_tree = atomicize(tree, User)
```
