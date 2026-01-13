# Shape Layer — Philosophy

The shape layer adds **declarative structure** to the term layer.

Shapes define topology. Slots build refs. Classes become schemas.

## Core Idea

Shapes are class-based structure definitions:

```python
class Order(Shape):
    price = FloatSlot()
    volume = IntSlot()

class Market(Shape):
    signal = FloatSlot()
    orders = ShapesDictSlot(Order)
```

Access creates refs:

```python
Market.signal              # → FloatRef
Market.orders["AAPL"]      # → ShapeRef[Order]
Market.orders["AAPL"].price # → FloatRef
```

No instances. No runtime objects. Just refs.

## The Components

| Component | What It Does |
|-----------|--------------|
| `Shape` | Base class with metaclass magic |
| `Slot` | Factory that creates Refs |

## Slots Are Factories

Slots don't hold data. They build refs.
The factory function returns a Slot but is typed as Ref for autocomplete.

## Slot Types

| Slot | Creates | For |
|------|---------|-----|
| `IntSlot()` | `IntRef` | Integer values |
| `StrSlot()` | `StrRef` | String values |
| `FloatSlot()` | `FloatRef` | Float values |
| `ListSlot(T)` | `ListRef[T]` | Lists of primitives |
| `DictSlot(V)` | `DictRef[K,V]` | Dicts of primitives |
| `ShapeSlot(S)` | `ShapeRef[S]` | Nested shape |
| `ShapesListSlot(S)` | `ShapesListRef[S]` | List of shapes |
| `ShapesDictSlot(S)` | `ShapesDictRef[S]` | Dict of shapes |

## Injection Points

Everything is injectable:

```python
# Custom view
DictSlot(float, view_type=MyCustomDictView)

# Custom ref via custom slot
class MoneySlot(Slot):
    def create_ref(self, ...) -> MoneyRef:
        return MoneyRef(...)

# Custom value type flows from custom ref
class MoneyRef(PrimitiveRef):
    def get(self) -> MoneyValue: ...
```

Inject views. Inject refs. Inject types. Shapes just wire them.

## Composition

Shapes compose infinitely:

```python
class Address(Shape):
    street = StrSlot()
    city = StrSlot()

class Person(Shape):
    name = StrSlot()
    home = ShapeSlot(Address)
    work = ShapeSlot(Address)

class Company(Shape):
    employees = ShapesDictSlot(Person)
    offices = ShapesListSlot(Address)
```

Navigate any depth:

```python
Company.employees["alice"].home.city  # → StrRef
Company.offices[0].street             # → StrRef
```

## What Shapes Are

- **Declarative** — define structure, not behavior
- **Static** — no instances, class-level only
- **Composable** — nest arbitrarily
- **Typed** — IDE autocomplete works

## What Shapes Are NOT

- **Not ORM models** — no database mapping
- **Not validators** — no runtime checks
- **Not serializers** — no encode/decode
- **Not instances** — never instantiated

Shapes define where data lives. Not what it means.

---

Classes as schemas. Slots as factories. Structure without behavior.
