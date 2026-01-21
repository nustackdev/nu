# Term Type System — Args & Ergonomics

Every input is either a literal or a computed value. The type system makes this uniform.

## The Core Pattern

```python
type Arg[T] = T | Term[T] | Term[T | Sentinel]
```

Three forms, one meaning:

- `T` — Python literal (`42`, `"hello"`, `datetime.now()`)
- `Term[T]` — Expression producing T (`price.get()`)
- `Term[T | Sentinel]` — Expression that might be empty/invalid

All are valid. All compose.

## Why Three, Not Two

`T | Term[T]` would be simpler. But storage operations return `Term[T | Sentinel]` — they might produce empty/invalid values. Accepting only `Term[T]` would force explicit unwrapping everywhere.

The third variant absorbs this. Sentinel handling moves downstream.

## Naming

```python
type IntArg = int | Term[int] | Term[int | Sentinel]
type StrArg = str | Term[str] | Term[str | Sentinel]
type FloatArg = float | Term[float] | Term[float | Sentinel]
# etc.
```

Pattern: `{Type}Arg`. No abbreviations. No suffixes beyond `Arg`.

Primitives have predefined aliases. Domain types define their own:

```python
# In datetime.py
type TimezoneArg = timezone | Term[timezone] | Term[timezone | Sentinel]
type DatetimeArg = datetime | Term[datetime] | Term[datetime | Sentinel]
```

## Usage in Methods

Every method parameter that accepts user input uses an Arg type:

```python
class StrType(Type[str]):
    def find(self, sub: StrArg, start: IntArg = 0) -> IntType:
        ...

    def replace(self, old: StrArg, new: StrArg, count: IntArg = -1) -> StrType:
        ...
```

Both work:
```python
s.find("x")              # Literal
s.find(other.get())      # Expression
s.find("x", pos.get())   # Mixed
```

## Type Names: `*Type`, Not `*Value`

All wrapped types end in `Type`:

| Class | Wraps |
|-------|-------|
| `IntType` | `int` |
| `StrType` | `str` |
| `DatetimeType` | `datetime` |
| `DecimalType` | `Decimal` |
| `UUIDType` | `UUID` |

The suffix signals: this is a term-layer wrapper, not the Python primitive.

`*Value` was legacy. `*Type` is consistent with the layer name (type system).

## Ref Names

Refs match their types:

| Ref | Returns |
|-----|---------|
| `IntRef` | `IntType` |
| `StrRef` | `StrType` |
| `DatetimeRef` | `DatetimeType` |

Pattern: `{Type}Ref` returns `{Type}Type`.

## Slot Names

Slots are factory functions returning refs:

```python
class Event(Shape):
    created_at = DatetimeSlot()  # Returns DatetimeRef
    name = StrSlot()             # Returns StrRef
```

Pattern: `{Type}Slot()` → `{Type}Ref`.

## Creating Custom Types

```python
from everyshape.term import Term, StrArg
from everyshape.types import BaseType
from everyshape.typing import Sentinel

# 1. Define the arg type
type MoneyArg = Money | Term[Money] | Term[Money | Sentinel]

# 2. Define the type class
class MoneyType(Type[Money | Sentinel]):
    @classmethod
    def from_cents(cls, cents: IntArg) -> MoneyType:
        return cls(FuncCallOp(Money.from_cents, cents))

    def to_cents(self) -> IntType:
        return IntType(MethodCallOp(self, "to_cents"))

# 3. Define the ref
class MoneyRef(PrimitiveRef):
    def set(self, value: MoneyArg) -> MoneyType:
        return MoneyType(TypedSetCmd(self, literal(value)))

    def get(self) -> MoneyType:
        return MoneyType(GetOp(self))

# 4. Define the slot
def MoneySlot() -> MoneyRef:
    return _MoneySlot()
```

Four pieces. One pattern. Every domain type follows this.

## What Arg Types Enable

**Composition without ceremony:**

```python
# All equivalent in ergonomics
datetime.replace(year=2024)
datetime.replace(year=year_ref.get())
datetime.replace(year=computed_year)
```

**Type checking catches misuse:**

```python
datetime.replace(year="2024")  # Type error: str is not IntArg
```

**Self-documenting APIs:**

```python
def from_timestamp(cls, ts: FloatArg, tz: TimezoneArg | None) -> DatetimeType
```

The signature tells you: `ts` accepts floats or float-producing expressions. `tz` accepts timezones or timezone-producing expressions, or nothing.

## Non-Goals

- **Not for internal APIs** — Ops receive concrete terms, not args
- **Not for return types** — Methods return `IntType`, not `IntArg`
- **Not for validation** — Runtime still needs `literal()` conversion

Arg types are ergonomic sugar for method signatures. They make user code clean. Internal plumbing uses concrete types.

---

Literals and expressions are interchangeable. The type system makes this invisible. Users write natural code. The library handles the unification.
