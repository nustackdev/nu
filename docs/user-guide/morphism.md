# Morphism

A Morphism is a transformation node. It answers: **how** inputs become outputs.

## Core Idea

Morphisms take children (other terms), resolve them, and apply a function. They are lazy — building one does nothing. Execution resolves children first, then calls `apply()`.

```python
class AddOp(BinaryOperation[int]):
    def apply(self, left: int, right: int) -> int:
        return left + right

expr = AddOp(User.age, 1)  # tree node, nothing runs
result = await expr.execute(ctx)  # resolves User.age, adds 1
```

## Operation vs Command

Two kinds of morphism, distinguished by purity:

- **Operation** — pure, no side effects. Safe to cache, reorder, parallelize.
- **Command** — impure, has side effects. Order matters.

```python
class UpperOp(UnaryOperation[str]):      # pure: always same result
    def apply(self, operand: str) -> str:
        return operand.upper()

class AppendCmd(BinaryCommand[list]):    # impure: mutates storage
    def apply(self, left: list, right: object) -> list:
        left.append(right)
        return left
```

## Arity

Morphisms come in three arities. Pick the one that matches your operand count:

| Base class | Operands | `apply()` signature |
|---|---|---|
| `UnaryOperation[T]` | 1 | `apply(self, operand) -> T` |
| `BinaryOperation[T]` | 2 | `apply(self, left, right) -> T` |
| `TernaryOperation[T]` | 3 | `apply(self, first, second, third) -> T` |

Same for commands: `UnaryCommand`, `BinaryCommand`, `TernaryCommand`.

## Writing a Morphism

### Step 1: Choose base class

Arity (how many operands) + purity (operation or command).

### Step 2: All operands are terms

Every operand passed to `super().__init__()` becomes a child in the tree. At execution time, each child is resolved to its Python value before `apply()` is called.

This means **all data operands must go through `__init__` as children** — not stored as instance attributes. Instance attributes are for non-data configuration like callables.

```python
# CORRECT: field is a term (resolved at runtime, can be dynamic)
class PluckOp(BinaryOperation[list]):
    def apply(self, left, right):  # left=collection, right=field name
        return [item[right] for item in left]

# WRONG: field is hardcoded (can never be a dynamic term)
class PluckOp(UnaryOperation[list]):
    def __init__(self, operand, field: str):
        super().__init__(operand)
        self._field = field  # frozen at construction time!
```

### Step 3: Callables are attributes

Callables (lambdas, functions) are transforms, not data. They configure *how* the morphism works, not *what* it works on. Store them as `_fn` attributes.

```python
class MapOp(UnaryOperation[list]):
    def __init__(self, operand: object, fn: Callable) -> None:
        super().__init__(operand)  # operand = child (resolved)
        self._fn = fn             # fn = config (not resolved)

    def apply(self, operand: object) -> list:
        return list(map(self._fn, operand))
```

### Step 4: Optional parameters

When two ops differ only by an optional parameter, merge them.

```python
# Good: one op with optional key
class MaxOp(UnaryOperation[T]):
    def __init__(self, operand: object, key: Callable | None = None) -> None:
        super().__init__(operand)
        self._key = key

    def apply(self, operand: object) -> T:
        return max(operand, key=self._key)

# Usage: max_() and max_(key=...) are the same op
items.max_()
items.max_(key=lambda x: x["price"])

# Bad: two separate ops for the same thing
class MaxOp(UnaryOperation[T]): ...    # max()
class MaxByOp(UnaryOperation[T]): ...  # max(key=fn)
```

### Step 5: Return INVALID on failure

When a morphism can't compute a result, return `INVALID` instead of raising. This lets the tree propagate failure gracefully.

```python
from everybase.core import INVALID, Sentinel

class PluckOp(BinaryOperation[list]):
    def apply(self, left: object, right: object) -> list | Sentinel:
        if not isinstance(left, Iterable):
            raise TypeError(f"pluck_() requires iterable, got {type(left).__name__}")
        try:
            return [item[right] for item in left]
        except (KeyError, TypeError):
            return INVALID
```

Rule of thumb: `TypeError` for wrong input types (programming error), `INVALID` for data-level failures (missing keys, empty sequences).

## Examples

### Unary — one operand

```python
class LenOp(UnaryOperation[int]):
    def apply(self, operand: object) -> int:
        return len(operand)
```

### Binary — two operands

```python
class PluckOp(BinaryOperation[list]):
    """Extract field from each element: [x[key] for x in seq]."""

    def apply(self, left: object, right: object) -> list | Sentinel:
        try:
            return [item[right] for item in left]
        except (KeyError, TypeError):
            return INVALID
```

### Ternary — three operands

```python
class FilterByOp(TernaryOperation[list]):
    """Filter by field value: [x for x in seq if x[key] == value]."""

    def apply(self, first: object, second: object, third: object) -> list | Sentinel:
        try:
            return [item for item in first if item[second] == third]
        except (KeyError, TypeError):
            return INVALID
```

### With callable config

```python
class FilterOp(UnaryOperation[list]):
    """Filter by predicate."""

    def __init__(self, operand: object, fn: Callable) -> None:
        super().__init__(operand)
        self._fn = fn

    def apply(self, operand: object) -> list:
        return list(filter(self._fn, operand))
```

## Sentinel Propagation

If any child resolves to a sentinel (`EMPTY` or `INVALID`), the morphism returns `INVALID` without calling `apply()`. You don't need to handle this — the base class does it.

```
AddOp(user.age, EMPTY)  →  INVALID  (apply never called)
AddOp(user.age, 1)      →  apply(25, 1)  →  26
```

## Checklist

When writing a new morphism:

1. All data operands → children via `super().__init__()` (never store as `_attr`)
2. Callables → instance attributes (`_fn`, `_key_fn`)
3. Pick correct arity (Unary/Binary/Ternary)
4. Pick correct purity (Operation/Command)
5. Return `INVALID` for data failures, raise `TypeError` for programming errors
6. Merge related ops with optional params instead of creating separate classes
