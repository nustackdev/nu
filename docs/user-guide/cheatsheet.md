# Cheatsheet

Quick reference for all Types, Flows, and Ref operations across everybase, everyshape, and everypv.

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

### Special

| Type | Class | Purpose |
|------|-------|---------|
| `object` | `AnyValue` | Untyped wrapper |
| `Empty` | `EmptyValue` | Slot not yet written |
| `Invalid` | `InvalidValue` | Operation failed (data-level, not exception) |

---

## TypeBase Methods (all refs/values)

```python
ref.is_empty()       # → BoolValue
ref.is_invalid()     # → BoolValue
ref.is_sentinel()    # → BoolValue
ref.not_empty()      # → BoolValue
ref.not_invalid()    # → BoolValue
ref.to_int()         # → IntValue
ref.to_float()       # → FloatValue
ref.to_bool()        # → BoolValue
ref.to_str()         # → StrValue
ref.to_bytes()       # → BytesValue
ref.to_list()        # → ListValue
```

---

## Capability Methods

### Arithmetic (NumericBase)

```python
a + b                # AddOp
a - b                # SubOp
a * b                # MulOp
a / b                # TrueDivOp → FloatValue
a // b               # FloorDivOp → IntValue
a % b                # ModOp
a ** b               # PowOp
-a                   # NegOp
abs(a)               # AbsOp (via __abs__)
```

### Comparison (ComparableBase)

```python
a == b    a.eq(b)    # EqOp → BoolValue
a != b    a.ne(b)    # NeOp → BoolValue
a < b     a.lt(b)    # LtOp → BoolValue
a > b     a.gt(b)    # GtOp → BoolValue
a <= b    a.le(b)    # LeOp → BoolValue
a >= b    a.ge(b)    # GeOp → BoolValue
```

### Logical (LogicalBase)

```python
a.and_(b)            # AndOp → BoolValue
a.or_(b)             # OrOp → BoolValue
a.not_()             # NotOp → BoolValue
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
s.upper()            # → StrValue
s.lower()            # → StrValue
s.title()            # → StrValue
s.capitalize()       # → StrValue
s.swapcase()         # → StrValue
s.strip(chars?)      # → StrValue
s.lstrip(chars?)     # → StrValue
s.rstrip(chars?)     # → StrValue
s.split(sep?, max?)  # → ListValue
s.rsplit(sep?, max?) # → ListValue
s.find(sub)          # → IntValue
s.rfind(sub)         # → IntValue
s.count_substring(s) # → IntValue
s.startswith(pfx)    # → BoolValue
s.endswith(sfx)      # → BoolValue
s.isdigit()          # → BoolValue
s.isalpha()          # → BoolValue
s.isalnum()          # → BoolValue
s.isspace()          # → BoolValue
s.center(w, fill?)   # → StrValue
s.ljust(w, fill?)    # → StrValue
s.rjust(w, fill?)    # → StrValue
s.zfill(w)           # → StrValue
s.replace(old, new)  # → StrValue
s.encode(enc?)       # → BytesValue
s + other            # → StrValue (concatenation)
s[i]                 # → StrValue (index)
s[i:j]               # → StrValue (slice)
```

---

## Collection Methods

### Iterable (shared by list, dict, set)

```python
c.len_()             # → IntValue
c.contains(item)     # → BoolValue
c.map_(fn)           # → CollectionValue (transform each element)
c.filter_(pred)      # → CollectionValue (keep matching)
c.filter_by_(fld, v) # → CollectionValue (keep where field == value)
c.reduce_(fn, init)  # → Value (fold)
c.pluck_(field)      # → CollectionValue (extract field from each element)
c.to_dict_(k_fn, v)  # → DictValue (build dict from elements)
c.sum_()             # → ElementValue
c.min_(key?)         # → ElementValue
c.max_(key?)         # → ElementValue
c.any_()             # → BoolValue
c.all_()             # → BoolValue
```

### Sequence (list, tuple)

```python
seq.first()              # → ElementValue
seq.last()               # → ElementValue
seq.reversed_()          # → CollectionValue
seq.sorted_(reverse?)    # → CollectionValue
seq.join(sep)            # → StrValue
seq.index(value)         # → IntValue
seq.find_index(pred)     # → IntValue
seq.count(value)         # → IntValue
seq[i]                   # → ElementValue (index)
seq[i:j]                 # → CollectionValue (slice)
seq + other              # → CollectionValue (concatenation)
```

### Mutable Sequence (list)

```python
seq.append(item)         # → CollectionValue
seq.extend(items)        # → CollectionValue
seq.insert(idx, item)    # → CollectionValue
seq.pop(idx?)            # → ElementValue
seq.remove(value)        # → CollectionValue
```

### Mapping (dict)

```python
d.keys_()                # → ListValue
d.values_()              # → ListValue
d.items_()               # → ListValue
d.get_(key, default?)    # → Value
d[key]                   # → AnyValue (subscript)
```

### Mutable Mapping (dict)

```python
d.set_(key, value)       # → Value
d.delete(key)            # → Value
d.update_(other)         # → CollectionValue
```

---

## PV Ref Types (everypv)

These are what you use in Shape slot definitions.

### Primitive Refs

```python
pv.IntRef.slot()         # int storage
pv.FloatRef.slot()       # float storage
pv.StrRef.slot()         # string storage
pv.BoolRef.slot()        # boolean storage
pv.BytesRef.slot()       # bytes storage
```

### Extended Refs

```python
pv.DateRef.slot()        # datetime.date
pv.DatetimeRef.slot()    # datetime.datetime
pv.TimeRef.slot()        # datetime.time
pv.TimedeltaRef.slot()   # datetime.timedelta
pv.DecimalRef.slot()     # decimal.Decimal
pv.FractionRef.slot()    # fractions.Fraction
pv.ComplexRef.slot()     # complex
pv.PercentageRef.slot()  # percentage
pv.BasisPointRef.slot()  # basis points
pv.PathRef.slot()        # pathlib.Path
pv.UUIDRef.slot()        # uuid.UUID
```

### Collection Refs

```python
pv.ListRef.slot(T)                     # list of T
pv.DictRef.slot(K, V)                  # dict with K keys, V values
pv.SetRef.slot(T)                      # set of T
pv.ShapeRef.slot(MyShape)              # single nested shape
pv.ShapesListRef.slot(MyShape)         # list of shapes
pv.ShapesDictRef.slot(MyShape)         # dict of shapes (str keys)
pv.ShapesDictRef.slot(MyShape, key_type=int)  # dict of shapes (int keys)
```

---

## PV Ref Operations (everyshape capabilities)

### Item Refs (primitive slots)

```python
ref.get()                # → typed Value (read from storage)
ref.set(value)           # → typed Value (write to storage)
ref.exists()             # → BoolValue (slot has been written)
ref.missing()            # → BoolValue (slot not yet written)
ref.remove()             # → NoneValue (delete from storage)
```

### Collection Refs (list, dict, set, shape refs)

```python
ref.get()                # → typed Value (extract entire collection)
ref.store(data)          # → typed Value (replace entire collection)
ref.exists()             # → BoolValue
ref.missing()            # → BoolValue
ref.clear()              # → NoneValue (remove all entries)
```

### Reactive (observation triggers)

Primitive refs:
```python
ref.on_change()          # OnPrimitiveChangeOp — fires when this value changes
```

Collection/view refs:
```python
ref.on_change()              # OnChangeOp — any change in this view
ref.on_child_change(addr)    # OnChildChangeOp — specific child changed
ref.on_children_change()     # OnChildrenChangeOp — any immediate child changed
ref.on_descendants_change()  # OnDescendantsChangeOp — any descendant changed
```

### Navigation (document model)

```python
dict_ref[key]            # → child ref (navigates into dict)
list_ref[idx]            # → child ref (navigates into list)
shape_ref.field          # → child ref (navigates into shape slot)
```

---

## Flows (everybase.abc.flows)

```python
import everybase.abc.flows as f
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
| `ForEach` | `ForEach(items, body, *, index=ref)` | Iterate collection |
| `ForEachParallel` | `ForEachParallel(items, body, max_parallel=N)` | Concurrent iteration |

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
| `Retry` | `Retry(body, max_attempts=3, delay=0, backoff=1.0, on_retry=None)` | Retry with backoff |
| `Assert` | `Assert(cond, message="...")` | Validate condition |

### Timing

| Flow | Signature | Description |
|------|-----------|-------------|
| `Delay` | `Delay(seconds, body=None)` | Sleep, then optionally execute |
| `Timeout` | `Timeout(seconds, body, on_timeout=None)` | Time-limited execution |
| `Throttle` | `Throttle(interval, body=None)` | Rate-limit calls |
| `Debounce` | `Debounce(delay, body=None)` | Wait for quiet period |

### Reactive (everyshape)

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
f.AssertExists(ref)              # raises if missing
f.AssertMissing(ref)             # raises if exists
f.AssertEmpty(ref)               # raises if not empty
f.AssertNotEmpty(ref)            # raises if empty
f.AssertEquals(ref, value)       # raises if not equal
f.AssertNotEquals(ref, value)    # raises if equal
f.AssertGreaterThan(ref, value)  # raises if not >
f.AssertLessThan(ref, value)     # raises if not <
f.SkipIfEmpty(ref, body)         # skip body if empty
f.SkipIfNotEmpty(ref, body)      # skip body if not empty
f.SkipIfMissing(ref, body)       # skip body if missing
f.SkipIfExists(ref, body)        # skip body if exists
```

---

## Morphism Helpers (everybase.abc)

```python
from everybase.abc import FuncCallOp, MethodCallOp, GetAttrOp

# Call a Python function (escape hatch — prefer term algebra)
result = FuncCallOp(my_func, arg1, arg2)

# Call a method on a resolved object
result = MethodCallOp(obj_term, "method_name", arg1)

# Access an attribute
result = GetAttrOp(obj_term, "attr_name")
```

---

## Shape Declaration

```python
from everyshape import Shape
import everypv as pv

class MyState(Shape):
    counter = pv.IntRef.slot()
    name = pv.StrRef.slot()
    items = pv.ListRef.slot(str)
    records = pv.ShapesDictRef.slot(RecordShape)
    nested = pv.ShapeRef.slot(NestedShape)

# Access: MyState.counter, MyState.name, etc.
# These are class-level refs — Shape is never instantiated.
```

---

## Common Patterns

### Ref arithmetic in flows

```python
# Refs support operators — results are lazy terms
MyState.count.set(MyState.count + 1)
MyState.total.set(MyState.a + MyState.b * 2)
f.If(MyState.count > 10, handle_overflow)
```

### Dict navigation

```python
# Navigate into nested shapes
token = s.tokens[mint_key]        # → Token shape ref
block = token.blocks[slot_num]    # → TokenBlock shape ref
tx = block.txs[sig]               # → Transaction shape ref

# Then access fields
token.tx_count.set(token.tx_count + 1)
```

### FuncCallOp for unavoidable Python

```python
# When term algebra can't express it yet
filtered = FuncCallOp(my_filter_fn, raw_data)
s.buffer.store(filtered)

# Wrap in typed value when needed
count = IntValue(FuncCallOp(len, some_list))
```

### Service terms

```python
# Service methods return lazy terms
slot = Services.solana.get_slot()           # not called yet
block = Services.solana.get_block(slot)     # composed lazily
s.current_slot.set(slot)                    # evaluated at execution
```

### Type methods via term algebra

```python
# Domain types wrap service results
curve = BondingCurveValue(Services.pumpfun.get_bonding_curve(mint))
s.market_cap.set(curve.market_cap())        # MethodCallOp under the hood
s.price.set(curve.price())                  # resolved at execution
```
