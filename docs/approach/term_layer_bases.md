# Term Layer — Bases

Bases are **implementations**. They provide behavior for capabilities.

Mix and match. No inheritance trees.

## Ref Bases

Implementation mixins for storage operations:

| Base | Implements | Methods |
|------|------------|---------|
| `ExistableBase` | `Existable` | `exists()`, `missing()` |
| `GettableBase` | `Gettable` | `get()` |
| `SettableBase` | `Settable` | `set(v)` |
| `DeletableBase` | `Deletable` | `remove()` |
| `ExtractableBase` | `Extractable` | `extract()` |
| `StorableBase` | `Storable` | `store(v)` |
| `ClearableBase` | `Clearable` | `clear()` |
| `LengthableBase` | `Lengthable` | `length()` |

### Sequence Bases

| Base | Methods |
|------|---------|
| `SequenceIndexableBase` | `[index]`, `[slice]` |
| `SequenceIterableBase` | `map()`, `filter()`, `reduce()`, `find()` |
| `AppendableBase` | `append(v)` |
| `InsertableBase` | `insert(i, v)` |
| `PoppableBase` | `pop()` |

### Mapping Bases

| Base | Methods |
|------|---------|
| `MappingNestableBase` | `[key]` navigation |
| `KeysQueryableBase` | `keys()` |
| `ValuesQueryableBase` | `values()` |
| `ItemsQueryableBase` | `items()` |
| `MappingIterableBase` | `map_values()`, `filter()`, `find_key()` |
| `MappingAccessibleBase` | `get_item()`, `set_item()`, `remove_item()` |

### Observable Bases

| Base | Methods |
|------|---------|
| `PrimitiveObservableBase` | `on_change()` for leaf values |
| `ViewObservableBase` | `on_change()`, `on_child_change()`, `on_descendants_change()` |

## Value Bases

Implementation mixins for computations:

### Core

| Base | Methods |
|------|---------|
| `CoreBase` | `ifelse()`, `is_empty()`, `is_invalid()`, `or_default()`, `to_*()` |

### Arithmetic

| Base | Methods |
|------|---------|
| `AddableBase` | `+` |
| `SubtractableBase` | `-` |
| `NegatableBase` | unary `-`, `+`, `abs()` |
| `AdditiveBase` | Combines Add + Sub + Negatable |
| `MultiplyableBase` | `*` |
| `DivisibleBase` | `/`, `//` |
| `ModuloableBase` | `%` |
| `PowerableBase` | `**` |
| `MultiplicativeBase` | Combines Mul + Div + Mod + Pow |
| `NumericBase` | Combines all arithmetic |

### Comparison & Logic

| Base | Methods |
|------|---------|
| `OrderableBase` | `>`, `<`, `>=`, `<=` |
| `EqualableBase` | `eq()`, `ne()` |
| `ComparisonBase` | Combines Orderable + Equalable |
| `AndableBase` | `and_()` |
| `OrableBase` | `or_()` |
| `NotableBase` | `not_()` |
| `LogicalBase` | Combines all logical |

### Collections

| Base | Methods |
|------|---------|
| `LengthableBase` | `len_()` |
| `IndexableBase` | `[index]` |
| `SliceableBase` | `[start:stop]` |
| `ContainableBase` | `contains()` |
| `IterableBase` | `map_()`, `filter_()`, `reduce_()` |
| `SequenceBase` | Combines for lists |
| `MappingBase` | Combines for dicts |

## Composite Ref Bases

Pre-assembled for common patterns:

| Base | For |
|------|-----|
| `CollectionItemRefBase` | Leaf values in containers |
| `MutableSequenceRefBase` | List-like refs |
| `MutableMappingRefBase` | Dict-like refs |
| `MutableSetRefBase` | Set-like refs |

## Usage Pattern

```python
# Value: pick capabilities
class MoneyValue(
    NumericBase,       # +, -, *, /
    ComparisonBase,    # >, <, ==
    CoreBase,          # ifelse, is_empty
    TypedValue[Money],
):
    def to_cents(self) -> IntType: ...

# Ref: use composite base
class MoneyRef(
    CollectionItemRefBase[Money, MoneyValue],
    PrimitiveRef,
):
    def get(self) -> MoneyValue: ...
    def set(self, v) -> MoneyValue: ...
```

---

Atomic bases. Composite bases. Mix what you need.
