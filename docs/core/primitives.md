# Primitives

## Unit

Base for all tree nodes.

```python
class Unit(ABC):
    """Node in the execution tree."""

    def needs(self) -> list[type[Context]]:
        """Context types I require."""
        return []

    def children(self) -> list[Unit]:
        """My child units."""
        return []

    @abstractmethod
    def run(self, ctx: ContextMap) -> Any:
        """Execute with resolved contexts."""
        ...
```

---

## Term — Point

A computation. Produces a value. Children are Terms only (closed algebra).

```python
class Term[T](Unit, ABC):
    """Computation node. Returns a value."""

    def children(self) -> list[Term]:
        return []

    @abstractmethod
    def run(self, ctx: ContextMap) -> T:
        ...
```

Two fundamental kinds:

```
Term[T]
├── Ref[T]        — location ("where")
│   ├── Gettable
│   └── Settable
└── Morphism[T]   — transformation ("what")
    └── NAryMorphism[T]
        ├── UnaryMorphism[T]
        ├── BinaryMorphism[T]
        └── TernaryMorphism[T]
```

Orthogonal purity dimension:

```
Operation  — pure  (no side effects, cacheable)
Command    — impure (side effects, order-dependent)
```

---

## Flow — Path

Ordering between units. Controls traversal. Children are any Units.

```python
class Flow(Unit, ABC):
    """Ordering node. Controls execution order of children."""

    def children(self) -> list[Unit]:
        return []

    @abstractmethod
    def run(self, ctx: ContextMap) -> Any:
        ...
```

Concrete flows:

| Flow | Semantics |
|------|-----------|
| `Seq(a, b, c)` | Execute in order. |
| `Par(a, b, c)` | Execute concurrently. |
| `Cond(pred, then, else_)` | Branch on predicate. |
| `Loop(pred, body)` | Repeat while predicate holds. |

---

## Group — Region

Cohesion boundary. Declares that children share a property.
Children are any Units. Transparent — passes through child value.

```python
class Group(Unit, ABC):
    """Cohesion boundary. Children share a declared property."""

    def children(self) -> list[Unit]:
        return []

    @abstractmethod
    def run(self, ctx: ContextMap) -> Any:
        ...
```

Concrete groups:

| Group | Semantics |
|-------|-----------|
| `GroupedContext(ctx_type, children)` | Children share one context of `ctx_type`. |
| `RootGroup(substrates, children)` | Program-lifetime group. Holds substrate factories. |

`Atomic(children)` is sugar for `GroupedContext` with inferred context type:
- Only reads in subtree → Snapshot
- Any writes in subtree → Transaction
- No context needs → no-op
