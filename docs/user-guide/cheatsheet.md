# Cheatsheet

Quick reference for all Types, Values, Flows, Refs, and functional operations across everybase, everybase.shape, and eb-virtuals.

## Value Types (everybase)

All values are lazy — they build term trees, not compute immediately.

### Primitives

| Type | Class | Capabilities |
|------|-------|-------------|
| `int` | `IntValue` | Numeric, Comparable, Logical, Bitwise |
| `float` | `FloatValue` | Numeric, Comparable, Logical |
| `bool` | `BoolValue` | Comparable, Logical |
| `str` | `StrValue` | Addable, Comparable, Logical, Lengthable, Sliceable, Containable |
| `bytes` | `BytesValue` | Addable, Comparable, Lengthable, Sliceable, Containable |
| `None` | `NoneValue` | — |

### Collections

| Type | Class | Capabilities |
|------|-------|-------------|
| `list[T]` | `ListValue[T]` | Sequence + Mutable + Comparable |
| `dict[K,V]` | `DictValue[K,V]` | Mapping + Mutable + Comparable |
| `set[T]` | `SetValue[T]` | Set + Mutable + Comparable |
| `tuple[*Ts]` | `TupleValue[*Ts]` | Comparable |
| `frozenset[T]` | `FrozenSetValue[T]` | Set + Comparable |

### Collection Views

| Type | Class | Purpose |
|------|-------|---------|
| `dict_keys` | `DictKeysValue[K]` | Lazy dict keys view (set-like), `.to_list()` to materialize |
| `dict_values` | `DictValuesValue[V]` | Lazy dict values view, `.to_list()` to materialize |
| `dict_items` | `DictItemsValue[K,V]` | Lazy dict items view (set-like), `.to_list()` to materialize |
| `Iterator[T]` | `IteratorValue[T]` | Lazy iterator, `.to_list()` to materialize |

### Special

| Type | Class | Purpose |
|------|-------|---------|
| `object` | `AnyValue` | Untyped wrapper |
| `Empty` | `EmptyValue` | Slot not yet written |
| `Invalid` | `InvalidValue` | Operation failed (data-level, not exception) |

---

## Object[T] Methods (all refs/values)

The universal base provides sentinel checks only:

```python
ref.is_empty()       # -> BoolValue
ref.is_invalid()     # -> BoolValue
ref.is_sentinel()    # -> BoolValue
ref.not_empty()      # -> BoolValue
ref.not_invalid()    # -> BoolValue
```

---

## Capability Methods

### Arithmetic (NumericBase)

```python
a + b                # AddOp
a - b                # SubOp
a * b                # MulOp
a / b                # TrueDivOp -> FloatValue
a // b               # FloorDivOp -> IntValue
a % b                # ModOp
a ** b               # PowOp
-a                   # NegOp
abs(a)               # AbsOp (via __abs__)
```

### Comparison (ComparableBase)

```python
a == b    a.eq(b)    # EqOp -> BoolValue
a != b    a.ne(b)    # NeOp -> BoolValue
a < b                # LtOp -> BoolValue
a > b                # GtOp -> BoolValue
a <= b               # LeOp -> BoolValue
a >= b               # GeOp -> BoolValue
```

### Logical (LogicalBase)

```python
a.and_(b)            # AndOp -> BoolValue
a.or_(b)             # OrOp -> BoolValue
a.not_()             # NotOp -> BoolValue
a.bool_()            # BoolOp -> BoolValue
```

### Bitwise (BitwiseBase)

```python
a & b                # BitwiseAndOp
a | b                # BitwiseOrOp
a ^ b                # BitwiseXorOp
~a                   # BitwiseInvertOp
a << b               # LeftShiftOp
a >> b               # RightShiftOp
```

---

## String Methods (StrType)

```python
s.upper()            # -> StrValue
s.lower()            # -> StrValue
s.title()            # -> StrValue
s.capitalize()       # -> StrValue
s.swapcase()         # -> StrValue
s.strip(chars?)      # -> StrValue
s.lstrip(chars?)     # -> StrValue
s.rstrip(chars?)     # -> StrValue
s.split(sep?, max?)  # -> ListValue
s.rsplit(sep?, max?) # -> ListValue
s.find(sub)          # -> IntValue
s.rfind(sub)         # -> IntValue
s.count_substring(s) # -> IntValue
s.startswith(pfx)    # -> BoolValue
s.endswith(sfx)      # -> BoolValue
s.isdigit()          # -> BoolValue
s.isalpha()          # -> BoolValue
s.isalnum()          # -> BoolValue
s.isspace()          # -> BoolValue
s.center(w, fill?)   # -> StrValue
s.ljust(w, fill?)    # -> StrValue
s.rjust(w, fill?)    # -> StrValue
s.zfill(w)           # -> StrValue
s.replace(old, new)  # -> StrValue
s.encode(enc?)       # -> BytesValue
s + other            # -> StrValue (concatenation)
s[i]                 # -> StrValue (index)
s[i:j]               # -> StrValue (slice)
```

---

## Collection Methods

### Sequence (list, tuple)

```python
seq.first()              # -> ElementValue
seq.last()               # -> ElementValue
seq.join(sep)            # -> StrValue
seq.index(value)         # -> IntValue
seq.find_index(pred)     # -> IntValue
seq.count(value)         # -> IntValue
seq[i]                   # -> ElementValue (index)
seq[i:j]                 # -> CollectionValue (slice)
```

### Mutable Sequence (list)

```python
seq.append(item)         # -> NoneValue
seq.extend(items)        # -> NoneValue
seq.insert(idx, item)    # -> NoneValue
seq.pop(idx?)            # -> ElementValue
seq.remove(value)        # -> NoneValue
seq.clear()              # -> NoneValue
```

### Mapping (dict)

```python
d.keys()                 # -> DictKeysValue (set-like view)
d.values()               # -> DictValuesValue
d.items()                # -> DictItemsValue (set-like view)
d.get(key, default?)     # -> ValueResult
d.key_at(idx)            # -> ValueResult
d[key]                   # -> ValueResult (subscript)
```

### Mutable Mapping (dict)

```python
d.set(key, value)        # -> NoneValue
d.delete(key)            # -> NoneValue
d.update(other)          # -> NoneValue
d.pop(key, default?)     # -> ValueResult
d.popitem()              # -> ValueResult
d.setdefault(key, def?)  # -> ValueResult
d.clear()                # -> NoneValue
d.copy()                 # -> ValueResult
```

### Set (set, frozenset)

```python
s.union(other)               # -> SetValue
s.intersection(other)        # -> SetValue
s.difference(other)          # -> SetValue
s.symmetric_difference(other)# -> SetValue
s.issubset(other)            # -> BoolValue
s.issuperset(other)          # -> BoolValue
s.isdisjoint(other)          # -> BoolValue
```

### Mutable Set (set)

```python
s.add(value)                 # -> NoneValue
s.remove(value)              # -> NoneValue
s.discard(value)             # -> NoneValue
s.pop()                      # -> ElementValue
s.clear()                    # -> NoneValue
s.update(other)              # -> NoneValue
s.intersection_update(other) # -> NoneValue
s.difference_update(other)   # -> NoneValue
```

---

## Functional Operations (everybase.abc.fn)

All higher-order operations are standalone functions, not methods on collections.

```python
from everybase.abc import fn
```

### Transformations (lazy -- return IteratorValue)

```python
fn.Map(iterable, func)              # transform each element
fn.Filter(iterable, pred)           # keep matching elements
fn.Reversed(iterable)               # reverse order
fn.Flatten(iterable)                # flatten one level
fn.Unique(iterable, key=None)       # deduplicate preserving order
fn.Pluck(iterable, field)           # extract field from each element
fn.FilterBy(iterable, field, value) # keep where field == value
```

### Combinators (lazy -- return IteratorValue)

```python
fn.Zip(*iterables)                  # zip multiple iterables
fn.Chain(*iterables)                # concatenate iterables
fn.Enumerate(iterable, start=0)     # add index to each element
```

### Slicing (lazy -- return IteratorValue)

```python
fn.Take(iterable, n)                # first N elements
fn.Drop(iterable, n)                # skip first N elements
```

### Terminals (eager -- return concrete values)

```python
fn.Sorted(iterable, reverse=False)  # -> ListValue
fn.GroupBy(iterable, key_fn)        # -> ListValue[tuple[K, list]]
fn.Partition(iterable, pred)        # -> TupleValue[list, list]
fn.Reduce(iterable, fn, initial)    # -> AnyValue
fn.Sum(iterable)                    # -> AnyValue
fn.Min(iterable, key=None)          # -> AnyValue
fn.Max(iterable, key=None)          # -> AnyValue
fn.Any(iterable)                    # -> BoolValue
fn.All(iterable)                    # -> BoolValue
```

### Builtins

```python
fn.Len(obj)                         # -> IntValue
fn.Contains(collection, item)       # -> BoolValue
```

### Materializers

```python
fn.ToList(iterable)                 # -> ListValue (consume iterator)
fn.ToSet(iterable)                  # -> SetValue
fn.ToDict(iterable, key_fn, val_fn) # -> DictValue
```

---

## eb-virtuals Ref Types

These are what you use in Shape slot definitions.

### Primitive Refs

```python
ebv.IntRef.slot()         # int storage
ebv.FloatRef.slot()       # float storage
ebv.StrRef.slot()         # string storage
ebv.BoolRef.slot()        # boolean storage
ebv.BytesRef.slot()       # bytes storage
```

### Extended Refs

```python
ebv.DecimalRef.slot()     # decimal.Decimal
ebv.FractionRef.slot()    # fractions.Fraction
ebv.ComplexRef.slot()     # complex
ebv.BasisPointRef.slot()  # basis points
ebv.PercentageRef.slot()  # percentage
ebv.DateRef.slot()        # datetime.date
ebv.DatetimeRef.slot()    # datetime.datetime
ebv.TimeRef.slot()        # datetime.time
ebv.TimedeltaRef.slot()   # datetime.timedelta
ebv.TimezoneRef.slot()    # datetime.timezone
ebv.PathRef.slot()        # pathlib.Path
ebv.UUIDRef.slot()        # uuid.UUID
```

### Collection Refs

```python
ebv.ListRef.slot(item_type=str)                      # list of str
ebv.DictRef.slot(value_type=float)                    # dict with str keys, float values
ebv.DictRef.slot(value_type=float, key_type=int)      # dict with int keys, float values
ebv.SetRef.slot(item_type=str)                        # set of str
ebv.ShapeRef.slot(MyShape)                            # single nested shape
ebv.ShapesListRef.slot(MyShape)                       # list of shapes
ebv.ShapesDictRef.slot(MyShape)                       # dict of shapes (str keys)
ebv.ShapesDictRef.slot(MyShape, key_type=int)         # dict of shapes (int keys)
```

---

## Ref Operations (everybase.shape)

Refs ARE terms -- executing a ref reads its value directly (no separate `.get()` needed).

### Item Refs (primitive slots)

```python
ref.store(value)         # -> NoneValue (write to storage)
ref.exists()             # -> BoolValue (slot has been written)
ref.missing()            # -> BoolValue (slot not yet written)
ref.erase()              # -> NoneValue (delete from storage)
await ref.execute(ctx)   # read value from storage (ref is the term)
```

### Collection Refs (list, dict, set, shape refs)

```python
ref.store(data)          # -> NoneValue (replace entire collection)
ref.exists()             # -> BoolValue
ref.missing()            # -> BoolValue
ref.erase()              # -> NoneValue (delete from parent)
```

### Facets (eb-virtuals lazy/eager)

```python
ref.lazy                 # -> ref copy with lazy facet (default)
ref.eager                # -> ref copy with eager facet
```

### Navigation (document model)

```python
dict_ref[key]            # -> child ref (navigates into dict)
list_ref[idx]            # -> child ref (navigates into list)
shape_ref.field          # -> child ref (navigates into shape slot)
```

### Reactive (observation triggers -- everybase.shape)

Primitive refs:
```python
ref.on_change()          # OnPrimitiveChangeOp -- fires when this value changes
```

Collection/view refs:
```python
ref.on_change()              # OnChangeOp -- any change in this view
ref.on_child_change(addr)    # OnChildChangeOp -- specific child changed
ref.on_children_change()     # OnChildrenChangeOp -- any immediate child changed
```

---

## Flows (everybase.abc.flows)

```python
from everybase.abc.flows import Seq, If, Print  # etc.
# or
from everybase.abc import Print, Seq, fn
```

### Control

| Flow | Signature | Description |
|------|-----------|-------------|
| `Seq` | `Seq(*children)` | Execute sequentially |
| `If` | `If(cond, then, else_=None)` | Conditional branch |
| `While` | `While(cond, body)` | Loop while true |
| `DoWhile` | `DoWhile(cond, body)` | Body runs at least once |
| `Forever` | `Forever(body)` | Infinite loop |
| `Switch` | `Switch(sel, cases={...}, default=None)` | Multi-way branch |

### Iteration

| Flow | Signature | Description |
|------|-----------|-------------|
| `ForRange` | `ForRange(start, stop, body, *, step=1, index=ref)` | Counted loop |
| `ForEach` | `ForEach(items, body, *, item=ref, index=ref)` | Iterate collection |
| `Fold` | `Fold(items, *, acc=ref, initial=val, item=ref, body=...)` | Stateful reduction |

### Parallel

| Flow | Signature | Description |
|------|-----------|-------------|
| `Parallel` | `Parallel(*children)` | All run concurrently |
| `Race` | `Race(*children)` | First to finish wins |
| `All` | `All(*children)` | All must succeed |
| `Any` | `Any(*children)` | First success wins |

### Error Handling

| Flow | Signature | Description |
|------|-----------|-------------|
| `TryCatch` | `TryCatch(body, catch=None, finally_=None)` | Exception handling |
| `Retry` | `Retry(body, max_attempts=3, delay=0, backoff=1.0, on_attempt_fail=None)` | Retry with backoff |
| `Assert` | `Assert(cond, message="...")` | Validate condition |

### Timing

| Flow | Signature | Description |
|------|-----------|-------------|
| `Delay` | `Delay(seconds, body=None)` | Sleep, then optionally execute |
| `Timeout` | `Timeout(seconds, body, on_timeout=None)` | Time-limited execution |
| `Throttle` | `Throttle(interval, body=None)` | Rate-limit calls |
| `Debounce` | `Debounce(delay, body=None)` | Wait for quiet period |

### Reactive (everybase.shape.flows)

```python
from everybase.shape.flows.reactive import React, ReactForever, ReactWhile
```

| Flow | Signature | Description |
|------|-----------|-------------|
| `React` | `React(change, body=None, changed_key=ref)` | React once |
| `ReactForever` | `ReactForever(change, body, changed_key=ref)` | React forever |
| `ReactWhile` | `ReactWhile(change, cond, body, changed_key=ref)` | React while condition holds |

### I/O

| Flow | Signature | Description |
|------|-----------|-------------|
| `Print` | `Print(msg, *values)` | Print to stdout |
| `Log` | `Log(msg, level="info")` | Structured logging |
| `Debug` | `Debug(*values, labels=[...])` | Debug output |

### Assertion Helpers

```python
from everybase.abc.flows import (
    AssertExists, AssertMissing,
    AssertEmpty, AssertNotEmpty,
    AssertEquals, AssertNotEquals,
    AssertGreaterThan, AssertGreaterOrEqual,
    AssertLessThan, AssertLessOrEqual,
    SkipIfEmpty, SkipIfNotEmpty,
    SkipIfMissing, SkipIfExists,
)
```

---

## Morphism Helpers (everybase.abc)

```python
from everybase.abc import FuncCallOp, MethodCallOp, GetAttrOp

# Call a Python function (escape hatch -- prefer term algebra)
result = FuncCallOp(my_func, arg1, arg2)

# Call a method on a resolved object
result = MethodCallOp(obj_term, "method_name", arg1)

# Access an attribute
result = GetAttrOp(obj_term, "attr_name")
```

---

## Shape Declaration

```python
from everybase.shape import Shape
import eb_virtuals as ebv

class MyState(Shape):
    counter = ebv.IntRef.slot()
    name = ebv.StrRef.slot()
    items = ebv.ListRef.slot(item_type=str)
    records = ebv.ShapesDictRef.slot(RecordShape)
    nested = ebv.ShapeRef.slot(NestedShape)

# Access: MyState.counter, MyState.name, etc.
# These are class-level refs -- Shape is never instantiated.
```

---

## Common Patterns

### Lazy term composition

```python
# Refs compose lazily -- nothing touches storage until execute()
Seq(
    MyState.counter.store(0),
    MyState.name.store("hello"),
    Print("counter", MyState.counter),
    Print("upper name", MyState.name.upper()),
)
```

### Ref arithmetic in flows

```python
# Typed refs support operators -- results are lazy terms
MyState.counter.store(MyState.counter + 1)
If(MyState.counter > 10, handle_overflow)
```

### Dict navigation

```python
# Navigate into nested shapes
token = s.tokens[mint_key]        # -> Token shape ref
block = token.blocks[slot_num]    # -> TokenBlock shape ref
tx = block.txs[sig]               # -> Transaction shape ref

# Then access fields
token.tx_count.store(token.tx_count + 1)
```

### Lazy collection queries with fn

```python
Seq(
    Print("keys", my_dict.keys().to_list()),
    Print("first 2", fn.Take(my_dict.keys(), 2).to_list()),
    Print("sorted", fn.Sorted(my_dict.keys())),
    Print("has X?", fn.Contains(my_dict.keys(), "X")),
    Print("count", fn.Len(my_dict.keys())),
)
```

### FuncCallOp for unavoidable Python

```python
# When term algebra can't express it yet
filtered = FuncCallOp(my_filter_fn, raw_data)
s.buffer.store(filtered)

# Wrap in typed value when needed
count = IntValue(FuncCallOp(len, some_list))
```

### eb-virtuals execution

```python
from eb_virtuals.presets import memory_storage
from virtuals.tkv import StorageProtocol

with memory_storage() as storage:
    ctx = Context().bind(storage, StorageProtocol)
    await ebv.Atomic(
        Seq(
            MyState.counter.store(42),
            Print("val", MyState.counter),
        )
    ).execute(ctx)
```
