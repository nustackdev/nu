# Concepts and Rules

## Primitives

There are two kinds of nodes and one grouping mechanism:

- **Term** — *what*. Computes and returns a value. Children are Terms (closed algebra).
- **Flow** — *when*. Orders child execution. Returns nothing. Children can be Terms, Flows, or Spans.
- **Span** — *grouping*. Scopes context for children. Returns the last child's result (transparent). Children can be Terms, Flows, or Spans.

Span is dimensionless — it's a bracket, not a computational primitive.
The real structure is Term (what) and Flow (when), with Span as a transparent wrapper.

## Hierarchy

```text
Node[ChildT]                          # immutable tree node
 └── Executable[ChildT: Executable]   # typed subtree
      ├── Term[ResultT]               # computation (what)
      │    ├── LValue[T]              # addressable location
      │    │    └── Ref[T]            # typed reference
      │    └── RValue[ResultT]        # evaluable expression
      │         └── Morphism[T]       # transformation
      │              └── NAryMorphism[T]
      │                   ├── UnaryMorphism[T]
      │                   ├── BinaryMorphism[T]
      │                   └── TernaryMorphism[T]
      ├── Flow                        # ordering (when)
      └── Span                        # grouping (context boundary)
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

### Node Initialization Contract

Every class in the Node hierarchy **must** call `super().__init__()` with its children. Failing to do so leaves `_children` uninitialized, which silently breaks tree traversal, purity detection, and any operation that walks the tree.

```python
# CORRECT - children are registered via super().__init__()
class MyOp(Operation, Morphism[int]):
    def __init__(self, ref, value):
        super().__init__(ref, value)
        self.ref = ref
        self.value = value

# WRONG - _children is never set
class MyOp(Operation, Morphism[int]):
    def __init__(self, ref, value):
        self.ref = ref
        self.value = value
```

This is especially dangerous because the error only surfaces when something traverses *through* that node. Spans walk the entire subtree to check purity — a single missing `_children` anywhere in the tree crashes the span before any child executes.

---

## Term

Computation node. Produces a value when executed.

```text
Term[ResultT](Executable, ABC)
  abstract  execute(ctx)    -> ResultT
  abstract  is_self_pure    -> bool       # this node only
  concrete  is_subtree_pure -> bool       # self + all descendant Terms
```

Children are Terms (closed algebra — computation doesn't impose order).

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

Ordering node. Controls when children execute. Returns nothing.

```text
Flow(Executable[Executable], ABC)
  concrete  execute(ctx) -> None          # sequential by default
```

Children can be Terms, Flows, or Spans (anything that needs ordering).

Concrete flows:

| Flow | Semantics |
|------|-----------|
| `Seq(a, b, c)` | Execute in order |
| `Par(a, b, c)` | Execute concurrently |
| `Cond(pred, then, else_)` | Branch on predicate |
| `Loop(pred, body)` | Repeat while predicate holds |

---

## Span

Grouping node. Scopes context for children. Returns the last child's result.

```text
Span(Executable[Executable], ABC)
  concrete  enter(ctx)                -> Context    # scope context (default: passthrough)
  concrete  exit_success(ctx)         -> None       # cleanup on success (default: noop)
  concrete  exit_failure(ctx, error)  -> None       # cleanup on failure (default: noop)
  concrete  execute(ctx)              -> object     # enter -> run children -> exit; returns last result
```

Spans are transparent — removing a Span doesn't change what is computed,
only what is shared during computation. Returning the last child's result
is part of this transparency: inserting or removing a Span doesn't break
data flow.

Children can be Terms, Flows, or Spans.

---

## Context

Type-keyed handle container. Immutable (returns new Context on mutation).

```text
Context
  [handle_type]                           -> T         # lookup, raises if missing
  [handle_type, scope]                   -> T         # lookup with scope
  .has(handle_type, scope=None)          -> bool
  .was_opened(handle_type, scope=None)   -> bool      # lazy factory was materialized

  .bind(handle, handle_type, scope=None)    -> Context   # eager
  .lazy(factory, handle_type, scope=None)   -> Context   # lazy
```

Key: `type` or `(type, scope)` for multi-store discrimination.

---

## Context Handles

Scoped resources consumed by Terms via Context. Any object can be used as a handle -- no base class required.

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

NAryMorphism.execute: if any resolved child is sentinel → return INVALID without calling apply.

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

### Meta-transforms (everybase.meta)

```text
conditional_wrap(root, pred, wrapper)   group contiguous matching children, wrap each group
```

### Query

```text
find(root, pred)       -> list[Node]       all matching (pre-order)
find_first(root, pred) -> Node | None      first matching
count(root, pred=None) -> int              count matching (None = all)
size(root)             -> int              total nodes
depth(root)            -> int              max depth (leaf = 0)
```

---

## Naming Conventions

| Concept | Naming | Examples |
|---------|--------|----------|
| Abstract ref | `*Type` | `IntType`, `StrType` |
| Concrete ref | `*Ref` | `PVIntRef`, `PVStrRef` |
| Pure morphism | `*Op` | `AddOp`, `EqOp`, `LenOp` |
| Impure morphism | `*Cmd` | `SetCmd`, `DeleteCmd` |
| Capability | Adjective | `Addable`, `Orderable`, `Gettable` |
| Compound capability | Noun | `Numeric`, `Comparable`, `Sequence` |

---

# Design Rules

The invariants we commit to. Labeled for cross-referencing.

## Composition

```
R1.  Term.children() → list[Term]           Terms compose only with Terms.
R2.  Flow.children() → list[Executable]     Flows compose with any Executable.
R3.  Span.children() → list[Executable]     Spans compose with any Executable.
```

The key constraint is one-directional: Flow can contain Terms
(ordering computation), but Terms can't contain Flows
(computation doesn't impose order). Span is orthogonal —
it wraps either.

## Structure

**S1. Span transparency.**
A Span is not a computation. It returns the last child's result.
Removing all Spans from a tree does not change what is computed,
only what is shared during computation.

**S2. Term closure.**
Composing Terms yields a Term. The Term algebra is closed.

**S3. Orthogonality.**
Term computes (what). Flow orders (when). Span groups (context).
Each primitive owns exactly one concern.

## Resolution

**B1. Needs propagate up.**
A node's needs are the union of its own needs and its children's needs.
Spans absorb the needs they provide — those don't propagate further.

**B2. Nearest enclosing Span wins.**
When a Term needs a context type, the executor walks up the tree.
First Span that provides a matching context wins.

**B3. Ephemeral fallback.**
If no Span provides what a Term needs, the executor creates
an ephemeral context from the nearest Substrate. Scoped to the
single expression.

**B4. Innermost wins.**
Nested Spans override. Inner Span's context shadows outer
for its subtree. Same mental model as variable scoping.

## Lifetime

**C1. Lazy open.**
A Span's context is created when the first child that needs it executes.
Not at Span entry.

**C2. Eager close.**
A Span's context is released when the last child that needed it completes.
Not at Span exit.

**C3. Context type inference.**
Atomic analyzes its subtree to pick the cheapest sufficient context:
only reads → Snapshot, any writes → Transaction, no needs → nothing opened.

## What Follows

**From S1:**
Spans can be inserted or removed without breaking data flow.
They only affect resource sharing and consistency guarantees.
The computation topology (Terms + Flows) is Span-invariant.

**From S3:**
Flow controls order. Span controls sharing. These compose freely.
`Atomic(Seq(...))` and `Seq(Atomic(...))` are both valid, mean different things.

**From B2 + B4:**
Context scoping is lexical. Innermost binding wins.

Note: Span-invariance holds cleanly for pure computations.
For impure computations, Spans affect consistency guarantees
(e.g., whether two writes are atomic), which may affect
observable outcomes. The *intent* of the computation is
preserved; the *guarantees* change.
