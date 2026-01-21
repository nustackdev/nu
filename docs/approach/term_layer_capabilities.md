# Term Layer — Capabilities

Capabilities are **protocols**. They declare what a type can do.

No implementation. Just interface.

## Two Worlds

| World | Protocols For | Example |
|-------|---------------|---------|
| **Refs** (LValue) | Storage operations | `Gettable`, `Settable`, `Extractable` |
| **Values** (RValue) | Computation | `Addable`, `Comparable`, `Indexable` |

## Ref Capabilities

Atomic operations on storage locations:

| Capability | Methods | Purpose |
|------------|---------|---------|
| `Existable` | `exists()`, `missing()` | Check presence |
| `Gettable` | `get()` | Read leaf value |
| `Settable` | `set(v)` | Write leaf value |
| `Deletable` | `remove()` | Delete value |
| `Extractable` | `extract()` | Read container |
| `Storable` | `store(v)` | Write container |
| `Clearable` | `clear()` | Empty container |
| `Lengthable` | `length()` | Container size |
| `Appendable` | `append(v)` | Add to sequence |
| `Insertable` | `insert(i, v)` | Insert in sequence |
| `Poppable` | `pop()` | Remove from sequence |
| `Nestable` | `[key]` | Navigate to child |
| `RefIndexable` | `[index]` | Index into sequence |
| `RefObservable` | `on_change()` | Watch for changes |

## Value Capabilities

Operators and methods on computed values:

| Capability | Methods | Purpose |
|------------|---------|---------|
| `Addable` | `+`, `__add__` | Addition |
| `Subtractable` | `-`, `__sub__` | Subtraction |
| `Multiplyable` | `*`, `__mul__` | Multiplication |
| `Divisible` | `/`, `//` | Division |
| `Orderable` | `>`, `<`, `>=`, `<=` | Ordering |
| `Equalable` | `eq()`, `ne()` | Equality |
| `Andable` | `and_()` | Logical AND |
| `Orable` | `or_()` | Logical OR |
| `Notable` | `not_()` | Logical NOT |
| `Indexable` | `[i]` | Index access |
| `Containable` | `contains()` | Membership |
| `Lengthable` | `len_()` | Collection size |

## Collection Protocols

Composed from atomic capabilities. Mirror Python's `collections.abc`:

```text
ContainerRef
└── CollectionRef (Extractable + Storable + Clearable + Lengthable)
    ├── SequenceRef (+ Indexable + Sliceable)
    │   └── MutableSequenceRef (+ Appendable + Insertable + Poppable)
    ├── MappingRef (+ Nestable + Keys + Values + Items)
    │   └── MutableMappingRef
    └── SetRef
        └── MutableSetRef (+ add + remove)
```

## Primitive Ref Protocol

Leaf values (not containers):

```text
CollectionItemRef = Existable + Gettable + Settable + Deletable + Observable
```

The most common ref type. Holds `int`, `str`, `float`, etc.

## Protocol vs Implementation

```python
# Protocol (capability) - declares interface
class Gettable(Protocol):
    def get(self) -> RValue: ...

# Base (implementation) - provides behavior
class GettableBase:
    def get(self) -> RValue:
        return self.value_value_type(GetOp(self))
```

Protocols live in `capabilities.py` and `collections.py`.
Bases live in `bases/` directory.

## Composition

Refs compose capabilities:

```python
class DatetimeRef(
    CollectionItemRefBase[datetime, DatetimeValue],  # Composites
    PrimitiveRef,                                     # Term type
):
    ...
```

Values compose capabilities:

```python
class DatetimeValue(
    ComparisonBase["DatetimeValue"],  # >, <, >=, <=
    CoreBase,                          # ifelse, is_empty
    TypedValue[datetime],              # Term type
):
    ...
```

---

Protocols declare. Bases implement. Composition assembles.
