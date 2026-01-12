# Container Layer — Philosophy

The container layer adds **hierarchy semantics** to flat storage.

It interprets tuple keys as hierarchical locations, distinguishes containers from primitives, and enforces parent-child rules.

## Core Design

### Pure Functions, Storage Side Effects

All operations are **stateless functions**. The only side effect is storage mutation.

```python
create_container(path, structure, protocol, ctx)
delete_subtree(path, ctx)
get_node_info(path, ctx)
```

No classes hold state. The `Container` wrapper is optional convenience.

### Idempotent by Default

Operations are designed for safe re-execution:

- `create_container` → returns `True` if created, `False` if already exists (with compatible type)
- `delete_container` → silent delete
- `set_child_primitive` → silent overwrite

No "already exists" exceptions on creates. No "not found" exceptions on deletes.
Exceptions are reserved for **actual conflicts** (type mismatch) or **operational failures**.

## Module Organization

Operations are grouped by **semantic domain**, not by entity:

| Module | Purpose |
|--------|---------|
| `node_ops` | Node identification and info gathering |
| `validation_ops` | Rule enforcement, raises exceptions |
| `container_ops` | CRUD, children, tree traversal |
| `meta_ops` | Parallel metadata tree operations |

This separation enables:

- Testing validation logic in isolation
- Skipping validation for trusted internal paths
- Composing operations without re-validation

## Information vs Validation

Two distinct layers:

**Information layer** — gathers data, makes no decisions:

```python
info = get_node_info(path, ctx)           # NodeInfo with all data
parent_info = gather_parent_info(path, ctx)  # ParentChainInfo
```

**Validation layer** — checks conditions, raises on failure:

```python
validate_is_container(path, ctx)      # Raises PathTypeError
validate_parents_healthy(path, ctx)   # Raises PathTypeError
```

Information functions are always safe. Validation functions are explicit checkpoints.

## Naming Conventions

### Verbs

Reads:

- `get_*` — single value, returns data (never raises for missing)
- `exists_*` — existence check, returns bool
- `count_*` — returns integer

Iteration (all return generators):

- `iter_*` — explicit iterator (`iter_children`, `iter_descendants`)
- `walk_*` — tree traversal with structure (`walk_tree`)

Mutations (all silent, return None):

- `create_*` — idempotent create
- `delete_*` — idempotent remove
- `put_*` — create or overwrite

Validation:

- `validate_*` — assert condition, raises on failure
- `gather_*` — collect information without decisions

Note: Avoid `list_*` for generators — it implies returning a list. Use `iter_*` for iterators.

### Nouns

- `site` — tuple representing location of container/primitive
- `node` — any storage entry (container or primitive)
- `container` — node that can have children
- `primitive` — leaf node with value
- `child` — direct descendant (depth +1)
- `descendant` — any node below a site

### Words to Avoid

Location terms from other layers:
- ~~key~~ → use `site` (key is storage layer)
- ~~path~~ → use `site` (path is view layer)
- ~~ref~~ → use `site` (ref is shape layer)

Structural terms:
- ~~tree~~ → use `container` (less is more, no extra concepts)
- ~~subtree~~ → use `descendants` (explicit about what it means)

## Context Handling

Explicit context guards enforce access requirements:

```python
require_read_context(ctx)      # Snapshot or Transaction
require_write_context(ctx)     # WriteBatch or Transaction
require_readwrite_context(ctx) # Transaction only
```

No implicit context. No global state. Every operation declares what it needs.

## What Container Does NOT Do

- **No data structure semantics** — dict/list/set behavior is View layer
- **No business logic** — application rules are Shape layer
- **No query language** — filtering/aggregation built on top

Container layer is structural plumbing. It knows paths and types, not meaning.

---

Boring, explicit, composable.
