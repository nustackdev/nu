# Context Resolution

How Terms find their contexts. One mechanism, no special cases.

---

## Substrate and Context

Two layers:

```
Substrate  = factory   (long-lived, creates contexts)
Context    = handle    (scoped, used by terms)
```

A Substrate lives in a Group (typically RootGroup) and produces Contexts on demand.
A Context lives in a Group (any level) and is shared by that Group's children.

```
RootGroup ── holds Substrates (factories, program lifetime)
  └── Group ── holds Contexts (handles, group lifetime)
       └── Term ── consumes Contexts
```

---

## The resolution rule

When a Term needs a context, the executor walks up the tree:

```
1. Enclosing Group provides matching Context?
   → use it (shared)

2. No Group provides? Ancestor has matching Substrate?
   → create ephemeral Context from Substrate (exclusive to this expression)
   → auto-close after expression completes

3. Neither?
   → error: unresolved need
```

The Term never knows whether its context is shared or exclusive:

```python
class ReadCmd(Term[T]):
    needs = [KVContext]

    def run(self, ctx: ContextMap) -> T:
        return ctx[KVContext].get(self.key)  # agnostic to source
```

---

## Implicit grouping

Every direct Term child of a Flow is implicitly an Atomic group (rule S1).
A Term subtree is one expression — indivisible by default.

```python
# What the user writes:
Seq(
    Ref.current.set(Ref.market.symbols[-1].get() + 1),
    Ref.log.print(),
)

# What the executor sees:
Seq(
    Atomic(Ref.current.set(Ref.market.symbols[-1].get() + 1)),
    Atomic(Ref.log.print()),
)
```

Atomic infers the minimal context type from the subtree:
- Only reads → Snapshot (cheap)
- Any writes → Transaction (atomic)
- No context needs → nothing opened (no-op, zero cost)

Explicit Group is only needed for cohesion **across** expression boundaries:

```python
# Independent — each expression gets its own context:
Seq(
    read(a),          # implicit Atomic → Snapshot
    write(b, 1),      # implicit Atomic → Transaction
)

# Cohesive — explicit Group spans both expressions:
Atomic(
    read(a),          # shared Transaction ─┐
    write(b, 1),      #                     ─┘
)
```

---

## Lazy lifetime

A Group declares the **boundary** of possible sharing.
The executor determines the **actual** lifetime within that boundary.

- **Open** — first child that touches the context triggers creation
- **Close** — last child that needed it finishes → release

A Group is a capacity declaration, not a lifecycle instruction:

```python
GroupedContext(Transaction,
    compute(x),       # pure — no context needed, nothing opened yet
    read(a),          # needs KV → open transaction NOW
    transform(y),     # pure — tx stays open (more KV children ahead)
    write(b, y),      # last KV user → close transaction after this
    log("done"),      # no KV — tx already closed
)
```

---

## Context types

```python
class Context(ABC):
    """Handle with capabilities. Scoped to a Group."""

    @abstractmethod
    def release(self) -> None: ...

class Substrate(ABC):
    """Factory that creates Contexts."""

    @abstractmethod
    def create(self, ctx_type: type[Context]) -> Context: ...
```

Context types form a hierarchy. Subtypes satisfy parent needs:

```python
class KVContext(Context, ABC):
    """Key-value access."""

class Snapshot(KVContext):
    """Read-only KV access."""
    def get(self, key) -> Any: ...

class Transaction(KVContext):
    """Read-write atomic KV access."""
    def get(self, key) -> Any: ...
    def put(self, key, value) -> None: ...
    def commit(self) -> None: ...
```

A Term that `needs(KVContext)` is satisfied by either Snapshot or Transaction.
The Group or Atomic wrapper determines which.

---

## ContextMap

The execution context passed through the tree:

```python
ContextMap = dict[type[Context], Context]
```

The executor builds it as it walks:

```
RootGroup entry  → register substrates  → ctx = {KVSubstrate: kv}
  Group entry    → create from substrate → ctx = {KVSubstrate: kv, Transaction: tx}
    Term         → reads ctx[Transaction]
  Group exit     → release context       → ctx = {KVSubstrate: kv}
RootGroup exit   → release substrates    → ctx = {}
```

Inner Groups shadow outer. Innermost match wins. Same rule at every level.
