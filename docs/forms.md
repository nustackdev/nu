# Forms

A Form is what a fabric location holds, independent of where it lives (RocksDB, Python dict, remote). Concretely each Form is a `ScalarQuery` passthrough that carries a Python type, so it participates in the Nu tree while preserving type information for downstream ops.

Two layers:

- **ABCs** (`Form`, `ContainerForm`, `SizedForm`, `SequenceForm`, `MappingForm`, ...) - shared interfaces, not used directly.
- **Leaf Forms** - the concrete things you write in code. Listed below.

Core only - shapes and ext/ not included.

## Primitives

| Form         | Holds   | Capabilities                                                |
| ------------ | ------- | ----------------------------------------------------------- |
| AnyForm      | object  | dynamic - all operations, results stay AnyForm              |
| BoolForm     | bool    | logical, comparable                                         |
| IntForm      | int     | numeric, comparable, logical, bitwise                       |
| FloatForm    | float   | numeric, comparable, logical                                |
| StrForm      | str     | addable, sliceable, comparable, logical, string ops         |
| BytesForm    | bytes   | sliceable, comparable, logical, bytes ops                   |
| NoneForm     | None    | logical only                                                |
| SentinelForm | T       | base for sentinel interfaces (Empty, Invalid)               |
| EmptyForm    | Empty   | absence of a value (the EMPTY sentinel)                     |
| InvalidForm  | Invalid | invalid or undefined operation result (the INVALID sentinel) |

## Collections

| Form           | Holds              | Capabilities                                            |
| -------------- | ------------------ | ------------------------------------------------------- |
| ListForm       | list[T]            | mutable sequence, comparable                            |
| TupleForm      | tuple[*Ts]         | immutable sequence, heterogeneous, comparable           |
| SetForm        | set[T]             | mutable set, comparable                                 |
| FrozenSetForm  | frozenset[T]       | immutable set, comparable                               |
| DictForm       | dict[K, V]         | mutable mapping, comparable                             |
| DictKeysForm   | KeysView[K]        | set-like view over a DictForm; lazy, live               |
| DictValuesForm | ValuesView[V]      | collection view over a DictForm; iterable, sized        |
| DictItemsForm  | ItemsView[K, V]    | set-like view over a DictForm; lazy, live               |
| IteratorForm   | Iterator[T]        | lazy iterator; materialize via `to_list`/`to_set`/`to_tuple` |

## Operators

Forms overload Python operators to build Nu nodes — they don't execute, they compose.

### Subscript: `form[key]`

Defined on the ABCs, so every Form that should be subscriptable picks it up uniformly:

- `SequenceForm.__getitem__(int | slice)` — int builds `At(self, key)`, slice builds `Slice(self, start, stop, step)`. Inherited by `ListForm`, `TupleForm`, and any sequence-shaped Form (including `TupleAttrRef`).
- `MappingForm.__getitem__(key)` — builds `At(self, key)`. Inherited by `DictForm`, `DictAttrRef`, etc.
- `StrForm` / `BytesForm` keep their own `__getitem__` (they sit outside the `SequenceForm` hierarchy).

Sets and primitives are not subscriptable, by design. The result is wrapped via the leaf's `_wrap_element_result` / `_wrap_sliceable_result` / `_wrap_value_result` hook — for `DictForm` and `ListForm` that's `AnyForm` by default, so chained subscripts past one level need an explicit re-wrap (`nu.DictForm(d["a"])["b"]`).

Slice dispatch is purely `isinstance(key, slice)`: `f[1:5]` → `Slice`, everything else (int, str, Nu node, tuple) → `At`. `Slice` keeps `start`/`stop`/`step` as separate child nodes so the tree stays walkable.

### Equality: `==`, `!=`

`a == b` and `a != b` on a Form build `Eq(a, b)` / `Ne(a, b)` and return a `BoolForm`. They are DSL builders — they do not compare Python objects.

For structural tree equality (compare two Nu nodes by class + children), use `Nu.eq(other)` on the base class. It is reserved for tree comparison and currently raises `NotImplementedError` — wire it up before relying on it.

`__hash__` is preserved as `object.__hash__` on every Form so Forms remain usable as dict keys / in sets despite overriding `__eq__`.
