# The Item Ref Question: Values, Locations, and Bound/Unbound

## Three kinds of refs

```python
IntRef(42)              # immutable value — no location, no .set()
ListRef(["a", "b"])     # mutable value — has .append(), .clear() (object mutation)
d["key"]                # location — has .get(), .set(), .remove() (address mutation)
Person.age              # location — same, via Shape
```

These are genuinely different things:

1. **Immutable value** (IntRef, StrRef): holds a value or computation.
   No mutation possible — 42 is 42.

2. **Mutable collection value** (ListRef, DictRef): holds a mutable Python
   object. Collection-level mutations work (append, clear) because the
   underlying object is mutable. But you can't .set() the collection itself
   — it has no external address.

3. **Location** (DictItemRef, ListItemRef, PVItemRef): points to a position
   inside a collection. Can read (.get()) and write (.set()). Knows its
   parent collection and its key/index.

## Bound vs unbound

**Unbound** — anonymous value, lives nowhere addressable:
```python
x = IntRef(42)       # just 42, no address, can't write back
tags = ListRef([])   # a list object, can mutate it but nobody else can find it
```

**Bound** — located in a collection at a known address:
```python
d["name"]            # bound to d at key "name"
Person.age           # bound to Person's backing dict at "age"
```

Bound refs can be written to because they have an address to write to.
Unbound refs can only be used as values in computations.

## Why everybase needs location refs (not just PV)

Currently `tags[0]` returns `AnyRef(AtOp(tags, 0))` — a read-only value.
But mutation requires knowing WHERE to write:

```python
tags[0].set("replaced")   # needs to know: index 0, in tags
d["key"].set(42)           # needs to know: key "key", in d
```

AtOp is a one-way read. To support writes, `tags[0]` must return a
location ref — something that knows the address and parent:

```python
tags[0]           # → ListItemRef(index=0, parent=tags)
tags[0].get()     # → AnyRef(AtOp(tags, 0))      — read
tags[0].set("z")  # → SetItemCmd(tags, 0, "z")    — write
tags[0].remove()  # → DeleteItemCmd(tags, 0)       — delete
```

This is exactly what PVListRef already does (returns PVListItemRef).
Same pattern, different substrate.

## In-memory mutation examples

### Collection-level mutations (on the collection value itself)
```python
tags = ListRef(["a", "b"])
tags.append("c")        # → AppendCmd(tags, "c")
tags.clear()             # → ClearCmd(tags)
# execute: resolves tags → gets list object → calls list.append("c")
# Works because Python lists are mutable reference types
```

### Item-level mutations (via location refs)
```python
d = DictRef({"name": "Alice", "age": 30})
d["name"]                # → DictItemRef("name", parent=d)
d["name"].get()          # → StrRef(AtOp(d, "name"))
d["name"].set("Bob")     # → SetItemCmd(d, "name", "Bob")

tags = ListRef(["a", "b"])
tags[0]                  # → ListItemRef(0, parent=tags)
tags[0].set("z")         # → SetItemCmd(tags, 0, "z")
```

### Compound mutations (+=)
```python
# Bound location:
Person.age += 10
# → Person.age.set(Person.age.get() + IntRef(10))
# → SetItemCmd(backing, "age", AddOp(AtOp(backing, "age"), IntRef(10)))

# Unbound value:
x = IntRef(42)
x += 10  # doesn't make sense — x has no address to write to
```

## What this means for everybase

everybase needs:

```
Value refs (existing, extended with collection mutations):
  IntRef, StrRef, FloatRef, BoolRef, BytesRef
    — immutable values, no .set()
  ListRef[T]
    — mutable collection value
    — NEW: .append(v), .insert(i, v), .pop(i), .clear()
    — __getitem__ NOW returns ListItemRef (location), not AnyRef
  DictRef[K, V]
    — mutable collection value
    — NEW: .clear(), .update(other)
    — __getitem__ NOW returns DictItemRef (location), not AnyRef
  SetRef[T]
    — mutable collection value
    — NEW: .add(v), .remove(v), .discard(v), .clear()

Item location refs (NEW):
  DictItemRef[V](key, parent, value_type)
    — .get() → typed value ref
    — .set(v) → SetItemCmd
    — .exists() → ExistsOp
    — .remove() → DeleteItemCmd
  ListItemRef[V](index, parent, value_type)
    — same API

Mutation commands (NEW):
  SetItemCmd(collection, key, value)    — collection[key] = value
  DeleteItemCmd(collection, key)        — del collection[key]
  AppendCmd(collection, value)          — collection.append(value)
  InsertCmd(collection, index, value)   — collection.insert(index, value)
  PopCmd(collection, index)             — collection.pop(index)
  ClearCmd(collection)                  — collection.clear()
  AddCmd(collection, value)             — collection.add(value) (sets)
  RemoveCmd(collection, value)          — collection.remove(value) (sets)
  DiscardCmd(collection, value)         — collection.discard(value) (sets)
  UpdateCmd(collection, other)          — collection.update(other) (dicts/sets)

Location capability bases (NEW, abstract with hooks):
  LocationGettable[T]     — .get() via _make_get_op() hook
  LocationSettable[T]     — .set(v) via _make_set_cmd() hook
  LocationExistable       — .exists() via _make_exists_op() hook
  LocationDeletable       — .remove() via _make_delete_cmd() hook
```

## Relationship between everybase and every_pv item refs

```
everybase                          every_pv
  DictItemRef                        PVDictItemRef
    parent = DictRef                   parent = PVDictRef (view-backed)
    fetch: dict[key]                   fetch: navigate view hierarchy
    .get() → AtOp                      .get() → PV GetOp
    .set() → SetItemCmd                .set() → PV SetCmd

  ListItemRef                        PVListItemRef
    parent = ListRef                   parent = PVListRef (view-backed)
    fetch: list[index]                 fetch: navigate view hierarchy
    .get() → AtOp                      .get() → PV GetOp
    .set() → SetItemCmd                .set() → PV SetCmd
```

Same API. Same concept. Different substrate.

The location capability bases live in everybase (abstract hooks).
everybase item refs implement hooks with generic Python operations.
every_pv item refs implement hooks with PV-specific morphisms.

## PyShape

With everybase having DictRef + DictItemRef + mutation commands,
PyShape becomes straightforward:

```python
class Person(PyShape):
    name = PyStrSlot()   # → DictItemRef("name", parent=backing, value_type=str)
    age = PyIntSlot()    # → DictItemRef("age", parent=backing, value_type=int)

# Backing is a DictRef registered in context for this shape
state = DictRef({"name": "Alice", "age": 30})
ctx = Context().with_handle(dict, state, shape=Person)

# Read
await Person.name.get().execute(ctx)      # → "Alice"

# Write
await Person.age.set(31).execute(ctx)     # → state["age"] = 31

# Compose
await (Person.age.get() + 10).execute(ctx)  # → 41
```

PyShape is NOT reimplementing PV. It's using everybase's own DictRef +
DictItemRef with a Shape-driven structure on top. Simple, no PV dependency,
works with plain Python dicts.

PV adds: views, containers, transactions, reactivity, nested hierarchies,
petabyte-scale storage. PyShape is the lightweight alternative for
in-memory use.

## Does Value need to be re-separated from Ref?

The current merge (Value = Ref) works IF we accept that:
- IntRef(42) is technically an LValue (even though it's really a value)
- DictItemRef is also an LValue (and it actually IS one)
- The distinction lives in capabilities, not type hierarchy

This is pragmatically fine. The capability system enforces the real
distinctions (what has .set() and what doesn't).

Re-separating would be type-theoretically correct but creates:
- Naming churn (IntRef → IntVal? or IntRef stays and Ref means location?)
- Two "int-typed term" types that operations must accept
- API breakage across the entire codebase

Recommendation: keep the merge, let capabilities do the work, add
item location refs as new types alongside existing value refs.
