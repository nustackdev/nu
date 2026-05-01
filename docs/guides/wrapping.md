# Auto wrapping

Inject atomic boundaries (Snapshot, Transaction) into a Nu tree by reading its effect annotations. No manual `with Transaction():` at every mutation point. One pass over the tree wraps what needs wrapping.

This guide covers the **flow-based, bottom-up** strategy: `auto_flow_atomic`. It is the default wrapping pass for virtuals.

## The unit of wrapping

A **Flow** composes Commands. Sequential, Parallel, Race, IfDo, ForEachDo — all Flows. A Flow's direct children are the natural unit of mutation: each branch is one step the user wrote.

So the wrapping unit is a **Flow's direct child**, not the Flow as a whole. Wrapping the whole Flow would commit every branch under one transaction; wrapping each child commits per branch and lets the strategy decide independence.

## The rule

Walk the tree bottom-up. At each Flow, replace every direct child according to its tracked effects on virtuals refs:

| Effect on virtuals refs in scope | Replacement              |
| -------------------------------- | ------------------------ |
| any WRITE                        | `Transaction(child, scope=...)` |
| only READ or RESOLVE             | `Snapshot(child, scope=...)`    |
| none                             | leave as-is              |

Detection is purely effect-driven via `tracked_effects(child)` — no `isinstance(Command)` or `isinstance(Query)` checks. A Command without virtuals effects is left bare; a Query that holds a writing dynamic ref gets a Transaction. The classification follows what the subtree actually does.

Bottom-up order matters: inner Flows are processed before the outer Flow sees them, so when the outer pass runs each child is already in its final shape.

## Scope

`scope` filters which refs count.

- `scope=Shape` — only refs where `ref.get_root_shape() is Shape`. Other shapes' refs are invisible to this pass.
- `scope=None` (default) — any virtuals ref counts. Tag is `scope=None`.

The scope flows into the wrapper: `Transaction(child, scope=Shape)` opens a transaction against that shape's Navigator.

## Brackets already in the tree

Two scopes drive every decision:

- `scope_pass` — argument to `auto_flow_atomic`. `⊥` (None) or a concrete shape `S`.
- `scope_brace` — the `scope` of the existing Bracket the walker meets. `⊥` or a concrete shape `T`.

For a virtuals ref `r`, with `is`-identity throughout:

```
covers(⊥, r) ≡ true                  cares(⊥, r) ≡ true
covers(T, r) ≡ root_shape(r) is T    cares(S, r) ≡ root_shape(r) is S

uncovered(pass, brace, r) ≡ cares(pass, r) ∧ ¬covers(brace, r)
```

`uncovered` is the only thing that drives walker behavior. The brace's declared coverage subtracts from the pass's care set; the walker acts on the remainder.

### Decisions at a Bracket

- **descend** iff some `r` in the body could satisfy `uncovered`. Decided statically from `(scope_pass, scope_brace)` alone.
- **external-wrap** iff the Bracket is a Flow child *and* its tracked effects contain `≥1` uncovered ref.

### Matrix

| `scope_pass` | `scope_brace` | uncovered set inside brace | descend | external-wrap iff body has |
| ------------ | ------------- | -------------------------- | ------- | -------------------------- |
| `⊥`          | `⊥`           | `∅`                        | no      | —                          |
| `⊥`          | `T`           | refs with shape ≠ T        | yes     | ≥1 ref with shape ≠ T      |
| `S`          | `⊥`           | `∅`                        | no      | —                          |
| `S`          | `S`           | `∅`                        | no      | —                          |
| `S`          | `T` (`T ≠ S`) | refs with shape = S        | yes     | ≥1 ref with shape = S      |

Reduction: **descend ⇔ external-wrap-may-fire ⇔ uncovered set is non-empty.**

### Wrap kind and scope

When external-wrap fires, classify by uncovered effects only:

- WRITE through any uncovered ref → `Transaction(brace, scope=scope_pass)`
- only READ/RESOLVE through uncovered refs → `Snapshot(brace, scope=scope_pass)`

The new Bracket carries `scope_pass`. This yields nestings like `Tx(⊥, Tx(T, …))` or `Tx(S, Tx(T, …))`. Inside descended bodies the matrix applies recursively at every Flow.

## Multi-pass composition

Apply passes in any order:

```python
tree = auto_flow_atomic(tree, scope=LedgerA)   # wrap A's mutations
tree = auto_flow_atomic(tree, scope=LedgerB)   # wrap B's mutations, ignore A's
tree = auto_flow_atomic(tree)                   # default: fill any remaining gaps
```

Each pass sees the previous passes' Brackets and respects them by the rules above. Order does not change correctness — only the nesting shape.

## API

```python
from nu_virtuals.tree import auto_flow_atomic

wrapped = auto_flow_atomic(tree, scope=Ledger)
```

Underlying primitives in `nu.shapes.tree.wrap`:

| Name                 | Meaning                                                                 |
| -------------------- | ----------------------------------------------------------------------- |
| `wrap_flow_children` | At each Flow, replace each direct child via a callback. Bottom-up. Takes an optional `descend` predicate to mark subtrees opaque. |
| `wrap_flows`         | Wrap outermost Flows whole. Top-down. Used by `auto_total_atomic`.      |
| `is_flow`            | Predicate: node is a Flow.                                              |
| `touches_fabric`     | Predicate: subtree holds a Ref of given types.                          |
| `has_write_on_fabric`| Predicate: subtree has a WRITE through a Ref of given types.            |

The toolkit is fabric-agnostic. `auto_flow_atomic` is the virtuals-specific composition: `wrap_flow_children` + virtuals ref types + Snapshot/Transaction.

## When to reach for something else

- **Whole-Flow boundary.** Use `auto_total_atomic` — wraps each outermost virtuals-touching Flow as one Bracket. Coarser, single commit per Flow.
- **Per-Command boundary.** Use `auto_atomic` — wraps every individual virtuals-touching Command. Maximum granularity, smallest transactions.

`auto_flow_atomic` sits between the two: per-branch within Flows, respecting the structure the user already wrote.
