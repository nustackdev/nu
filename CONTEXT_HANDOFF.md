# Everybase Development Context Handoff

## What Was Built: everyast Package

Location: `abc/everyast/`

A pure tree library with node contracts. Two layers:

### AST Layer (`src/everyast/ast/`)
- `node.py` — `Node[_ChildT]` generic base with immutable operations (with_children, append, prepend, insert, remove, replace_child). Returns `Self` so subclasses get proper types.
- `walk.py` — Lazy generators: preorder, postorder, bfs, leaves, ancestors
- `transform.py` — Tree transforms: map_children, map_nodes, replace, wrap, unwrap, graft, prune, compose
- `query.py` — Tree queries: find, find_first, count, size, depth

### Defs Layer (`src/everyast/defs/`)
- `exec.py` — `Exec(Node["Exec"])` base for all typed nodes
- `term.py` — `Term(Exec, ABC)` with abstract `is_pure: bool` property
- `flow.py` — `Flow(Exec, ABC)` ordering constraints
- `span.py` — `Span(Exec, ABC)` cohesion boundaries (renamed from Hull)
- `sentinel.py` — `Empty`, `Invalid` singletons with type guards

**242 tests passing, ruff clean.**

## Key Design Decisions

1. **Tree not Graph**: Like compiler ASTs — tree is containment structure, sharing is metadata via names/ids resolved in separate pass

2. **Two-layer architecture**: everyast (pure tree + contracts) → everybase (concrete implementations). Old `every` and `everytree` packages moved to `_playground/`

3. **Generic Node**: `Node[_ChildT]` with `Self` returns so `Exec(Node["Exec"])` gives properly typed children/methods

4. **No topology language in everyast**: Terms like "topology", "0-cell/1-cell/2-cell" belong downstream in everybase, not in the abstract tree layer

5. **everyast has NO context mechanism**: Tree is pure topology. Context is runtime/execution concern in everybase.

## Current Design Direction: Context & Execution

### The Simple Model (agreed upon)

**Context = type-keyed bag of handles. No context algebra on the tree.**

```
User creates handles (clients, connections)
    ↓
User builds Context with those handles
    ↓
Executor threads Context through the tree
    ↓
Spans SHAPE context (open transaction from handle, pass down)
    ↓
Terms CONSUME context (look up handle by type, do work)
```

### Context Interface

```python
class Context:
    """Type-keyed handle container. Immutable."""

    def get[T](self, handle_type: type[T]) -> T: ...
    def has(self, handle_type: type) -> bool: ...
    def with_handle(self, handle_type: type, handle) -> Context: ...
```

No Handle base class. No Substrate factory. Just types as keys. User creates handles however they want.

### Spans as Context Shapers

Spans don't declare what they provide — they **transform context at execution time**:

```python
class Atomic(Span):
    def execute(self, ctx):
        kv = ctx.get(KVHandle)           # get substrate handle
        txn = kv.transaction()            # shape into transaction
        child_ctx = ctx.with_handle(Transaction, txn)
        try:
            result = execute_children(self, child_ctx)
            txn.commit()
            return result
        except:
            txn.rollback()
            raise
```

### No Multi-Context

Each Ref knows its handle type directly:
```python
class KVRef(Ref[T]):
    def fetch(self, ctx):
        txn = ctx.get(Transaction)  # knows exactly what it needs
        return txn.get(self.key)
```

The old `get_context_for_shape()` pattern goes away. Different stores = different handle types.

### Resumability as Metatool

Flows don't store state internally. A tree transform adds checkpointing:
```python
resumable_tree = add_checkpoints(tree, state_store)
```

This wraps nodes with state-dumping logic. Original tree stays clean.

### Snapshot vs Transaction

Determined by Term purity:
- Pure subtree (`is_pure=True` for all Terms) → Snapshot (read-only)
- Impure subtree (any `is_pure=False`) → Transaction (read-write)

Atomic can inspect subtree purity to auto-select context type.

## What Needs to Be Built

### everybase abstract layer
- `Context` — type-keyed handle container (immutable, with_handle pattern)
- `execute(tree, ctx)` — executor that threads context through tree
- `Atomic(Span)` — context shaper, opens transaction/snapshot from handle

### everybase concrete
- `Seq(Flow)`, `Par(Flow)`, `Cond(Flow)` — concrete flow types
- Concrete terms — LValue, RValue, Ref, Morphism hierarchy
- Integration with everyast walk/transform/query

### Reference code in _playground/
- `_playground/every/src/every/context.py` — old Context with type-keyed handles
- `_playground/every/src/every/executor.py` — old executor showing context threading
- `_playground/poc4/topology/context.py` — Snapshot/Transaction implementations

## File Locations

```
abc/everyast/           — DONE: pure tree + contracts
abc/everybase/          — TO BUILD: concrete implementations
std/every_pv/           — PV/KV specific context (has old KVContext)
pkgs/every_notion/      — Notion specific context (has old NotionContext)
_playground/every/      — old code for reference
_playground/everytree/  — old code for reference
_playground/poc4/       — POC code for reference
```

## Contributing Rules

- Python 3.10+
- Ruff for linting/formatting (check root pyproject.toml for rules)
- UV workspace (not pip)
- No backwards compat — break things during R&D
- Check `./contributing/` for full guidelines

## Key Insight Summary

The tree (everyast) is **pure topology** — just parent-child relationships and node type contracts. All runtime concerns (context, handles, execution, state) live in **everybase**. Spans are the bridge — structurally they're just grouping nodes, but at execution time they shape/scope context for their children.
