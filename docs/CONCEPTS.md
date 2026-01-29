# Concepts

Mental map of the core contracts.

---

## Hierarchy

```text
Node[ChildT]                          # immutable tree node
 └── Executable[ChildT: Executable]   # typed subtree
      ├── Term[ResultT]               # computation (0-cell)
      │    ├── LValue[T]              # addressable location
      │    │    └── Ref[T]            # typed reference
      │    └── RValue[ResultT]        # evaluable expression
      │         └── Morphism[T]       # transformation
      │              └── NAryMorphism[T]
      │                   ├── UnaryMorphism[T]
      │                   ├── BinaryMorphism[T]
      │                   └── TernaryMorphism[T]
      ├── Flow                        # ordering (1-cell)
      └── Span                        # cohesion boundary (2-cell)
```

Orthogonal purity mixins (first in MRO):

```text
Operation   is_self_pure = True
Command     is_self_pure = False
```

Pre-composed: `{NAry,Unary,Binary,Ternary}{Operation,Command}[T]`

---

## Node

Immutable generic tree node. All mutations return new nodes.

```text
Node[ChildT]
  # access
  .children          -> tuple[ChildT, ...]
  .child_count       -> int
  .is_leaf           -> bool
  .get_child(i)      -> ChildT
  .iter_children()   -> Iterator[ChildT]
  .has_child(c)      -> bool              # identity check

  # reconstruct
  .with_children(*c) -> Self              # override for extra state

  # mutate (immutable — returns new)
  .append_child(c)   -> Self
  .prepend_child(c)  -> Self
  .insert_child(i,c) -> Self
  .remove_child(i)   -> Self
  .replace_child(i,c)-> Self
```

---

## Term

Executable computation node. Leaf of the topology.

```text
Term[ResultT](Executable, ABC)
  abstract  execute(ctx)    -> ResultT
  abstract  is_self_pure    -> bool       # this node only
  concrete  is_subtree_pure -> bool       # self + all descendant Terms
```

### LValue / Ref

Addressable location with typed read.

```text
LValue[T](Term[T], ABC)
  abstract  resolve(ctx) -> object        # substrate-specific location

Ref[T](LValue[T | Sentinel], ABC)
  abstract  resolve(ctx) -> object
  abstract  fetch(ctx)   -> T | Sentinel
  concrete  execute(ctx) -> T | Sentinel  # delegates to fetch
  concrete  is_self_pure -> True          # reading never mutates
```

### Morphism

Transformation with operand resolution and sentinel propagation.

```text
Morphism[T](RValue[T], ABC)
  __init__(*children: object)             # wraps literals via ensure_term

NAryMorphism[T](Morphism[T | Sentinel], ABC)
  abstract  apply(*values)  -> T | Sentinel
  concrete  execute(ctx)    -> T | Sentinel   # resolve children -> apply

UnaryMorphism[T]    __init__(operand)         .operand
BinaryMorphism[T]   __init__(left, right)     .left  .right
TernaryMorphism[T]  __init__(first,sec,third) .first .second .third
```

Each arity narrows `apply`:

```text
UnaryMorphism.apply(operand)
BinaryMorphism.apply(left, right)
TernaryMorphism.apply(first, second, third)
```

### Purity

Two mixins, first in MRO:

```text
Operation.is_self_pure -> True    (deterministic, cacheable, reorderable)
Command.is_self_pure   -> False   (order-dependent, transactional)
```

`is_subtree_pure` on Term walks `_children` automatically.

---

## Flow

Ordering constraint. Controls how children execute.

```text
Flow(Executable[Executable], ABC)
  concrete  execute(ctx) -> None          # sequential by default, override for other strategies
```

---

## Span

Cohesion boundary. Shapes context for a subtree.

```text
Span(Executable[Executable], ABC)
  concrete  enter(ctx)                -> Context    # scope context (default: passthrough)
  concrete  exit_success(ctx)         -> None       # cleanup on success (default: noop)
  concrete  exit_failure(ctx, error)  -> None       # cleanup on failure (default: noop)
  concrete  execute(ctx)              -> None       # enter -> run children -> exit
```

---

## Context

Type-keyed handle container. Immutable (returns new Context on mutation).

```text
Context
  .get(handle_type, shape=None)          -> T         # lookup, raises if missing
  .has(handle_type, shape=None)          -> bool
  .was_opened(handle_type, shape=None)   -> bool      # lazy factory was materialized

  .with_handle(handle_type, handle, shape=None)   -> Context   # eager
  .with_factory(handle_type, factory, shape=None) -> Context   # lazy
```

Key: `type` or `(type, shape_type)` for multi-store discrimination.

---

## Handle

Scoped resource consumed by Terms via Context.

```text
Handle
  .release() -> None                     # override for cleanup
```

---

## Shape / Slot

Declarative structure definition. Substrate-agnostic.

```text
Shape                                    # marker base for structure definitions

Slot(ABC)
  .name              -> str | None       # set by metaclass
  abstract create_ref(owner_shape, parent_ref=None) -> Ref
```

---

## Sentinel

Special values for absent/invalid data. Propagated through morphisms.

```text
Sentinel
  ├── Empty     EMPTY      # value doesn't exist (not None)
  └── Invalid   INVALID    # operation not applicable

is_empty(v)    -> TypeGuard[Empty]
is_invalid(v)  -> TypeGuard[Invalid]
is_sentinel(v) -> TypeGuard[Sentinel]
propagate_special(*values) -> Invalid | Empty | None
```

NAryMorphism.execute: if any resolved child is sentinel -> return INVALID without calling apply.

---

## Tree Utilities

### Walk (lazy generators)

```text
preorder(root)         depth-first, root before children
postorder(root)        depth-first, children before root
bfs(root)              breadth-first
leaves(root)           leaf nodes only
ancestors(target,root) path from root to target, or None
```

### Transform (non-mutating, returns new trees)

```text
map_children(node, fn)              shallow: fn on each direct child
map_nodes(root, fn, order)          deep: fn on every node (bottom_up | top_down)
replace(root, pred, replacement)    replace matching nodes
wrap(root, pred, wrapper)           wrap matching nodes
unwrap(root, pred)                  splice out single-child wrappers
graft(root, target, subtree)        replace target by identity
prune(root, pred)                   remove matching subtrees
compose(*transforms)                left-to-right composition
apply(root, *transforms)            apply transforms in order
```

### Query

```text
find(root, pred)       -> list[Node]       all matching (pre-order)
find_first(root, pred) -> Node | None      first matching
count(root, pred=None) -> int              count matching (None = all)
size(root)             -> int              total nodes
depth(root)            -> int              max depth (leaf = 0)
```
