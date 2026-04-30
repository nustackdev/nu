# Forms

Every Form in the repo. A Form is what a fabric location holds - independent of where it lives (RocksDB, Python dict, remote).

This page is partial - filled below as samples to confirm direction.

## Primitives (sample)

| Form         | Holds        | Notes                                  |
| ------------ | ------------ | -------------------------------------- |
| AnyForm      | object       | escape hatch - any Python value        |
| NoneForm     | None         |                                        |
| BoolForm     | bool         |                                        |
| IntForm      | int          |                                        |
| FloatForm    | float        |                                        |
| StrForm      | str          | string ops via attached Queries        |
| BytesForm    | bytes        | byte ops via attached Queries          |
| EmptyForm    | Empty        | EMPTY sentinel                         |
| InvalidForm  | Invalid      | INVALID sentinel                       |

## Collections (sample)

| Form           | Holds              | Notes                                |
| -------------- | ------------------ | ------------------------------------ |
| ListForm       | list[T]            | ordered, mutable                     |
| TupleForm      | tuple[*Ts]         | heterogeneous, fixed-arity           |
| SetForm        | set[T]             | unordered, unique                    |
| FrozenSetForm  | frozenset[T]       | immutable set                        |
| DictForm       | dict[K, V]         |                                      |
| DictKeysForm   | dict_keys[K]       | view over a DictForm                 |
| DictValuesForm | dict_values[V]     | view over a DictForm                 |
| DictItemsForm  | dict_items[K, V]   | view over a DictForm                 |
| IteratorForm   | Iterator[T]        | one-shot stream                      |

> Slot layout column to be added once we agree on shape.
