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
