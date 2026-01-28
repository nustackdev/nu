# Topology Language

A program is a tree. The tree has three kinds of nodes.
Each kind owns one concern. They compose freely.

```
Term   — point   — what to compute
Flow   — path    — in what order
Group  — region  — what is shared
```

The tree is data. Building it does nothing.
An executor walks the tree and turns shape into execution.

---

## Why three

Every program answers three orthogonal questions:

1. **What** happens at each step? → Term
2. **When** does each step run relative to others? → Flow
3. **What resources** are shared across steps? → Group

These concerns are independent. Changing the order (Flow) doesn't
change the computation (Term). Adding shared context (Group) doesn't
change what is computed or in what order.

Each primitive owns exactly one question:

```
          computes?    orders?    shares?
Term         x
Flow                     x
Group                                x
```

---

## How they compose

Terms only compose with Terms — the algebra is closed.
Flows and Groups compose with anything.

```
Term.children   → list[Term]
Flow.children   → list[Unit]
Group.children  → list[Unit]
```

Nesting is free:

```python
RootGroup(substrates=[KV(RocksDB("/data"))],
    Seq(
        GroupedContext(Transaction,
            read(a),
            write(b, compute(x)),
        ),
        notify("done"),
    )
)
```

---

## The topological analogy

The names point, path, region come from CW-complexes in algebraic topology:

- **0-cell** (point) — a vertex. A Term is a point of computation.
- **1-cell** (edge) — connects vertices. A Flow defines ordering between points.
- **2-cell** (face) — a surface bounded by edges. A Group glues points
  into a cohesive region.

This analogy is intentional but informal. We use it for intuition
and vocabulary, not as a proof technique. The formal semantics
are in [formal.md](formal.md).

---

## What the user writes vs. what runs

The user writes topology — pure structure, no imperative details:

```python
app = Seq(
    Ref.current.set(Ref.market.symbols[-1].get() + 1),
    Ref.log.append("updated"),
)
```

The executor handles everything else: context creation, resource
lifecycle, transaction management, cleanup. The user declares
shape. The executor interprets it.
