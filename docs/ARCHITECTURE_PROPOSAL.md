# Architecture Proposal: every + everybase

## Core Hierarchy

```
Term[T]                          # Root - everything is a Term
├── Ref[T]                       # Location reference ("where")
└── Morphism[T]                  # Transformation ("what")
    └── NAryMorphism[T]
        ├── UnaryMorphism[T]
        ├── BinaryMorphism[T]
        └── TernaryMorphism[T]

# Orthogonal purity dimension:
Operation                        # Pure - no side effects
Command                          # Impure - has side effects
```

Concrete implementations compose arity + purity:
```python
class AddOp[T](BinaryMorphism[T], Operation):
    def _apply(self, left, right) -> T:
        return left + right

class SetCmd[T](BinaryMorphism[T], Command):
    def _apply(self, ref, value) -> T:
        ...
```

---

## Package Responsibilities

### `every` - Contracts

**What things ARE. Abstract definitions only.**

```
every/
├── term.py           # Term[T] - root class
├── ref.py            # Ref[T] - location reference
├── morphism.py       # Morphism, NAryMorphism, Unary/Binary/Ternary
├── purity.py         # Operation, Command (orthogonal mixins)
├── shape.py          # Shape, Slot, SlotDescriptor, ShapeMeta
├── context.py        # Context (execution environment)
├── sentinel.py       # Sentinel, Empty, Invalid, NotSet
├── arg.py            # Arg[T], IntArg, StrArg, ...
└── flow.py           # Flow, Runtime, Path
```

### `everybase` - Foundations

**How things WORK. Base implementations for building substrates.**

```
everybase/
├── traits/           # Capability interfaces
│   ├── arithmetic.py # Addable, Subtractable, Negatable, ...
│   ├── comparison.py # Orderable, Equalable
│   ├── logical.py    # Andable, Orable, Notable
│   ├── bitwise.py    # BitwiseAnd, Shiftable, ...
│   └── collection.py # Indexable, Lengthable, Sliceable, ...
│
├── refs/             # Abstract typed refs (traits + Gettable)
│   ├── int.py        # IntRefBase
│   ├── float.py      # FloatRefBase
│   ├── str.py        # StrRefBase
│   └── ...
│
├── morphisms/        # Concrete morphisms (was comps/)
│   ├── arithmetic.py # AddOp, SubOp, MulOp, ...
│   ├── comparison.py # EqOp, LtOp, GtOp, ...
│   ├── logical.py    # AndOp, OrOp, NotOp
│   └── ...
│
├── py/               # Python memory refs (concrete)
│   ├── int.py        # IntRef
│   ├── float.py      # FloatRef
│   ├── str.py        # StrRef
│   └── ...
│
└── util/
    ├── literal.py    # literal() helper
    └── combiners.py  # Combination utilities
```

### `std/` and `pkgs/` - Substrates

```
std/
├── every_kv/         # KV storage refs
├── every_pv/         # View layer refs
└── every_datetime/   # Datetime extensions

pkgs/
├── every_notion/     # Notion refs
└── every_postgres/   # Postgres refs
```

---

## Conceptual Model

### 1. Term (in `every/term.py`)

```python
class Term[T](ABC):
    """Root of the type hierarchy. Everything is a Term.

    Terms are the nodes in the computation graph.
    Two kinds: Refs (locations) and Morphisms (transformations).
    """

    @abstractmethod
    def execute(self, ctx: Context) -> T | Sentinel:
        """Execute this term in the given context."""
        ...
```

### 2. Ref (in `every/ref.py`)

```python
class Ref[T](Term[T]):
    """Location reference. Points to where a value lives.

    Refs are terms that denote locations, not computations.
    NOT all refs are gettable or settable - use protocols to check.
    """

    def execute(self, ctx: Context) -> T | Sentinel:
        """Refs execute by getting their value (if Gettable)."""
        if isinstance(self, Gettable):
            return self.get(ctx)
        raise TypeError(f"{self} is not Gettable")


@runtime_checkable
class Gettable[T](Protocol):
    """Protocol for refs that support value extraction."""
    def get(self, ctx: Context) -> T | Sentinel: ...


@runtime_checkable
class Settable[T](Protocol):
    """Protocol for refs that support value mutation."""
    def set(self, ctx: Context, value: T) -> Self: ...
```

### 3. Morphism Hierarchy (in `every/morphism.py`)

```python
class Morphism[T](Term[T], ABC):
    """Transformation. Maps inputs to outputs.

    Morphisms are terms that represent computations/transformations.
    They have operands (children) and produce results.
    """

    @abstractmethod
    def execute(self, ctx: Context) -> T | Sentinel:
        """Execute the transformation."""
        ...


class NAryMorphism[T](Morphism[T], ABC):
    """Base for morphisms with operands. Handles resolution and sentinels."""

    children: tuple[Term | Any, ...]

    def execute(self, ctx: Context) -> T | Sentinel:
        """Resolve operands, propagate sentinels, apply transformation."""
        values = []
        for child in self.children:
            val = self._resolve(child, ctx)
            if is_sentinel(val):
                return INVALID
            values.append(val)
        return self._apply(*values)

    def _resolve(self, operand: Any, ctx: Context) -> Any:
        """Resolve operand to value."""
        if isinstance(operand, Term):
            return operand.execute(ctx)
        return operand  # Literal value

    @abstractmethod
    def _apply(self, *values: Any) -> T | Sentinel:
        """Apply the transformation to resolved values."""
        ...


class UnaryMorphism[T](NAryMorphism[T], ABC):
    """Single operand morphism."""

    def __init__(self, operand: Term | Any):
        self.children = (operand,)

    @abstractmethod
    def _apply(self, operand: Any) -> T | Sentinel: ...


class BinaryMorphism[T](NAryMorphism[T], ABC):
    """Two operand morphism."""

    def __init__(self, left: Term | Any, right: Term | Any):
        self.children = (left, right)

    @abstractmethod
    def _apply(self, left: Any, right: Any) -> T | Sentinel: ...


class TernaryMorphism[T](NAryMorphism[T], ABC):
    """Three operand morphism."""

    def __init__(self, a: Term | Any, b: Term | Any, c: Term | Any):
        self.children = (a, b, c)

    @abstractmethod
    def _apply(self, a: Any, b: Any, c: Any) -> T | Sentinel: ...
```

### 4. Purity (in `every/purity.py`)

```python
class Operation:
    """Mixin marking a morphism as pure.

    Pure morphisms:
    - No side effects
    - Deterministic (same inputs → same output)
    - Cacheable
    - Order-independent
    """

    @property
    def is_pure(self) -> bool:
        return all(child.is_pure for child in self.children if isinstance(child, Term))


class Command:
    """Mixin marking a morphism as impure.

    Impure morphisms:
    - Has side effects (mutations, I/O)
    - May be non-deterministic
    - Order-dependent
    - Requires transactional context
    """

    @property
    def is_pure(self) -> bool:
        return False
```

### 5. Traits (in `everybase/traits/`)

Capability interfaces for refs.

```
ARITHMETIC
──────────
Addable           →  __add__, __radd__
Subtractable      →  __sub__, __rsub__
Negatable         →  __neg__, __pos__, __abs__
Multiplyable      →  __mul__, __rmul__
Divisible         →  __truediv__, __floordiv__
Powerable         →  __pow__, __rpow__
Moduloable        →  __mod__, __rmod__

Numeric = Addable + Subtractable + Negatable + Multiplyable + Divisible + Powerable + Moduloable


COMPARISON
──────────
Orderable         →  __lt__, __gt__, __le__, __ge__
Equalable         →  eq(), ne()

Comparable = Orderable + Equalable


LOGICAL
───────
Andable           →  and_()
Orable            →  or_()
Notable           →  not_()

Logical = Andable + Orable + Notable


BITWISE
───────
BitwiseAndable    →  __and__, __rand__
BitwiseOrable     →  __or__, __ror__
BitwiseXorable    →  __xor__, __rxor__
BitwiseNotable    →  __invert__
Shiftable         →  __lshift__, __rshift__

Bitwise = BitwiseAndable + BitwiseOrable + BitwiseXorable + BitwiseNotable + Shiftable


COLLECTION
──────────
Lengthable        →  len_()
Indexable         →  __getitem__
Sliceable         →  slice_()
Containable       →  contains()
Iterable          →  map_(), filter_(), reduce_()

Sequence = Lengthable + Indexable + Sliceable + Containable + Iterable
Mapping = Lengthable + Indexable + Containable + keys, values, items
SetLike = Lengthable + Containable + union, intersection, difference
```

### 6. Abstract Typed Refs (in `everybase/refs/`)

```python
class IntRefBase(Numeric, Bitwise, Comparable, Ref[int], Gettable[int], ABC):
    """Abstract int ref. Gettable with all int operations."""

    @abstractmethod
    def get(self, ctx: Context) -> int | Sentinel: ...

    def __add__(self, other: int | Term[int]) -> IntRef:
        from everybase.py import IntRef
        from everybase.morphisms import AddOp
        return IntRef(AddOp(self, other))

    def __gt__(self, other: int | Term[int]) -> BoolRef:
        from everybase.py import BoolRef
        from everybase.morphisms import GtOp
        return BoolRef(GtOp(self, other))

    # ... all operators return concrete PyRefs
```

### 7. Concrete Morphisms (in `everybase/morphisms/`)

```python
# arithmetic.py

class AddOp[T](BinaryMorphism[T], Operation):
    """Addition: left + right. Pure."""

    def _apply(self, left: Any, right: Any) -> T | Sentinel:
        try:
            return left + right
        except TypeError:
            return INVALID


class NegOp[T](UnaryMorphism[T], Operation):
    """Negation: -operand. Pure."""

    def _apply(self, operand: Any) -> T | Sentinel:
        try:
            return -operand
        except TypeError:
            return INVALID
```

```python
# comparison.py

class EqOp(BinaryMorphism[bool], Operation):
    """Equality: left == right. Pure."""

    def _apply(self, left: Any, right: Any) -> bool:
        return left == right
```

```python
# conditional.py

class IfElseOp[T](TernaryMorphism[T], Operation):
    """Conditional: if cond then a else b. Pure."""

    def _apply(self, cond: Any, if_true: T, if_false: T) -> T:
        return if_true if cond else if_false
```

### 8. Python Memory Refs (in `everybase/py/`)

```python
class IntRef(IntRefBase):
    """Concrete int ref in Python memory."""

    def __init__(self, source: int | Morphism[int]):
        self._source = source

    def get(self, ctx: Context) -> int | Sentinel:
        if isinstance(self._source, Morphism):
            return self._source.execute(ctx)
        return self._source
```

### 9. How It Works Together

```python
# Refs from different substrates
notion_price = NotionIntRef(...)   # Gettable Ref
kv_quantity = KVIntRef(...)        # Gettable Ref
tax = IntRef(5)                    # Gettable Ref (literal)

# Operations create Morphisms, wrapped in PyRefs
total = notion_price + kv_quantity + tax
# → IntRef(AddOp(AddOp(notion_price, kv_quantity), tax))
#          ^^^^^ BinaryMorphism + Operation (pure)

# Execute resolves the graph
total.get(ctx)  # → 130
```

---

## Sentinel System

```
Sentinel                # Base for special values
├── Empty               # Location has no value
└── Invalid             # Operation failed

NotSet                  # Distinct from None (optional params)
```

Sentinels propagate: any sentinel operand → `INVALID` result.

---

## Dependency Graph

```
┌─────────────────────────────────────────────────────────┐
│                      pkgs/*                             │
│     NotionIntRef(IntRefBase), PgIntRef(IntRefBase)      │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────┼─────────────────────────────────┐
│                      std/*                              │
│      KVIntRef(IntRefBase), ViewIntRef(IntRefBase)       │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────┼─────────────────────────────────┐
│                    everybase                            │
│  ┌────────────────────────────────────────────────┐     │
│  │ traits/      refs/         morphisms/  py/     │     │
│  │ Addable      IntRefBase    AddOp       IntRef  │     │
│  │ Orderable    StrRefBase    EqOp        StrRef  │     │
│  │ Indexable    ListRefBase   LenOp       ListRef │     │
│  └────────────────────────────────────────────────┘     │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────┼─────────────────────────────────┐
│                      every                              │
│  ┌────────────────────────────────────────────────┐     │
│  │ Term[T]             - root class               │     │
│  │ Ref[T]              - location reference       │     │
│  │ Gettable, Settable  - capability protocols     │     │
│  │ Morphism            - transformation base      │     │
│  │ NAry/Unary/Binary/TernaryMorphism              │     │
│  │ Operation, Command  - purity markers           │     │
│  │ Shape, Slot         - structure declaration    │     │
│  │ Sentinel, Empty     - special values           │     │
│  └────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

---

## Summary

```
every       = Contracts (Term, Ref, Morphism, Operation/Command, Shape, Sentinel)
everybase   = Foundations (traits, refs, morphisms, Python refs)
std/*       = Storage substrates (KV, Views)
pkgs/*      = External substrates (Notion, Postgres)
```

**Key principles:**

1. **Term** - root of everything
2. **Ref vs Morphism** - location vs transformation (orthogonal)
3. **Operation vs Command** - pure vs impure (orthogonal)
4. **Arity** - Unary/Binary/Ternary (structural)
5. **Composition** - `AddOp(BinaryMorphism, Operation)`
6. **Traits** - capability mixins for refs
7. **Protocol enforcement** - operations return PyRefs
