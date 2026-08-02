---
title: nu.forms
---

Typed value interfaces. A Form is what a fabric location holds, wrapped in a
fluent typed surface - `Int`, `Str`, `Dict`, ... Two layers:

- **Concrete Forms** - the leaf things you write in code (`from nu import Str`).
- **Abstract Form contracts** (`forms/collections/abc/`) - shared interfaces
  (`SequenceForm`, `MappingForm`, ...), not used directly. These KEEP the
  `Form` suffix; concrete Forms dropped it in the rename pass.

Interaction ops that live physically under `nu.forms` (str/bytes methods,
collection ABC interactions) are listed alongside their owning Form so the
whole module is searchable from one page.

## Primitives

`from nu import Any, Bool, Bytes, Float, Int, None_, Str`

| Name  | Sort | Signature   | Effect | Meaning                                                          |
| ----- | ---- | ----------- | ------ | ----------------------------------------------------------------- |
| Any   | Form | `Any(source)`   | pure   | dynamic/unknown interface - absorbing under all ops, results stay Any; comparison/logical yield Bool |
| Bool  | Form | `Bool(source)`  | pure   | boolean interface - logical + comparable                          |
| Int   | Form | `Int(source)`   | pure   | integer interface - numeric + comparable + logical + bitwise; int/float promotion on mixed arithmetic |
| Float | Form | `Float(source)` | pure   | float interface - numeric + comparable + logical                  |
| Str   | Form | `Str(source)`   | pure   | string interface - addable + sliceable + comparable + logical + string methods |
| Bytes | Form | `Bytes(source)` | pure   | bytes interface - sliceable + comparable + logical + bytes methods |
| None_ | Form | `None_(source=None)` | pure | none interface - logical only                                 |

`from nu import SentinelForm, EmptyForm, InvalidForm` (`forms/primitives/sentinel_.py`)

| Name         | Sort | Signature       | Effect | Meaning                                          |
| ------------ | ---- | --------------- | ------ | ------------------------------------------------- |
| SentinelForm | Form | `SentinelForm[T]`   | pure   | base for sentinel interfaces (Empty, Invalid) - not instantiated directly |
| EmptyForm    | Form | `EmptyForm()`   | pure   | wraps the EMPTY sentinel - absence of a value      |
| InvalidForm  | Form | `InvalidForm()` | pure   | wraps the INVALID sentinel - invalid/undefined op result |

## Str interactions

`forms/primitives/str_interactions.py` - all pure (str is immutable), every op is a ScalarQuery. Reached via `Str` methods (`.upper()`, `.strip()`, ...), not called directly.

| Name           | Sort        | Signature                                  | Effect | Meaning                          |
| -------------- | ----------- | ------------------------------------------- | ------ | --------------------------------- |
| Upper          | ScalarQuery | `Upper(operand)`                            | pure   | str.upper()                       |
| Lower          | ScalarQuery | `Lower(operand)`                            | pure   | str.lower()                       |
| Title          | ScalarQuery | `Title(operand)`                            | pure   | str.title()                       |
| Capitalize     | ScalarQuery | `Capitalize(operand)`                       | pure   | str.capitalize()                  |
| SwapCase       | ScalarQuery | `SwapCase(operand)`                         | pure   | str.swapcase()                    |
| Casefold       | ScalarQuery | `Casefold(operand)`                         | pure   | str.casefold()                    |
| IsDigit        | ScalarQuery | `IsDigit(operand)`                          | pure   | str.isdigit()                     |
| IsAlpha        | ScalarQuery | `IsAlpha(operand)`                          | pure   | str.isalpha()                     |
| IsAlnum        | ScalarQuery | `IsAlnum(operand)`                          | pure   | str.isalnum()                     |
| IsSpace        | ScalarQuery | `IsSpace(operand)`                          | pure   | str.isspace()                     |
| IsNumeric      | ScalarQuery | `IsNumeric(operand)`                        | pure   | str.isnumeric()                   |
| IsDecimal      | ScalarQuery | `IsDecimal(operand)`                        | pure   | str.isdecimal()                   |
| IsIdentifier   | ScalarQuery | `IsIdentifier(operand)`                     | pure   | str.isidentifier()                |
| IsPrintable    | ScalarQuery | `IsPrintable(operand)`                      | pure   | str.isprintable()                 |
| IsTitle        | ScalarQuery | `IsTitle(operand)`                          | pure   | str.istitle()                     |
| IsUpper        | ScalarQuery | `IsUpper(operand)`                          | pure   | str.isupper()                     |
| IsLower        | ScalarQuery | `IsLower(operand)`                          | pure   | str.islower()                     |
| IsAscii        | ScalarQuery | `IsAscii(operand)`                          | pure   | str.isascii()                     |
| Strip          | ScalarQuery | `Strip(operand, chars)`                     | pure   | str.strip(chars)                  |
| LStrip         | ScalarQuery | `LStrip(operand, chars)`                    | pure   | str.lstrip(chars)                 |
| RStrip         | ScalarQuery | `RStrip(operand, chars)`                    | pure   | str.rstrip(chars)                 |
| Split          | ScalarQuery | `Split(operand, sep, maxsplit)`             | pure   | str.split(sep, maxsplit)          |
| RSplit         | ScalarQuery | `RSplit(operand, sep, maxsplit)`            | pure   | str.rsplit(sep, maxsplit)         |
| SplitLines     | ScalarQuery | `SplitLines(operand, keepends)`             | pure   | str.splitlines(keepends)          |
| Find           | ScalarQuery | `Find(operand, sub, start, end)`            | pure   | str.find(sub, start, end)         |
| RFind          | ScalarQuery | `RFind(operand, sub, start, end)`           | pure   | str.rfind(sub, start, end)        |
| Index          | ScalarQuery | `Index(operand, sub, start, end)`           | pure   | str.index(sub, start, end), Invalid if absent |
| RIndex         | ScalarQuery | `RIndex(operand, sub, start, end)`          | pure   | str.rindex(sub, start, end), Invalid if absent |
| CountSubstring | ScalarQuery | `CountSubstring(operand, sub)`              | pure   | str.count(sub)                    |
| StartsWith     | ScalarQuery | `StartsWith(operand, prefix)`               | pure   | str.startswith(prefix)            |
| EndsWith       | ScalarQuery | `EndsWith(operand, suffix)`                 | pure   | str.endswith(suffix)              |
| Center         | ScalarQuery | `Center(operand, width, fillchar)`          | pure   | str.center(width, fillchar)       |
| LJust          | ScalarQuery | `LJust(operand, width, fillchar)`           | pure   | str.ljust(width, fillchar)        |
| RJust          | ScalarQuery | `RJust(operand, width, fillchar)`           | pure   | str.rjust(width, fillchar)        |
| ZFill          | ScalarQuery | `ZFill(operand, width)`                     | pure   | str.zfill(width)                  |
| ExpandTabs     | ScalarQuery | `ExpandTabs(operand, tabsize)`              | pure   | str.expandtabs(tabsize)           |
| Partition      | ScalarQuery | `Partition(operand, sep)`                   | pure   | str.partition(sep), 3-tuple       |
| RPartition     | ScalarQuery | `RPartition(operand, sep)`                  | pure   | str.rpartition(sep), 3-tuple      |
| Replace        | ScalarQuery | `Replace(operand, old, new, count)`         | pure   | str.replace(old, new, count)      |
| RemovePrefix   | ScalarQuery | `RemovePrefix(operand, prefix)`             | pure   | str.removeprefix(prefix)          |
| RemoveSuffix   | ScalarQuery | `RemoveSuffix(operand, suffix)`             | pure   | str.removesuffix(suffix)          |
| Translate      | ScalarQuery | `Translate(operand, table)`                 | pure   | str.translate(table)              |
| FormatMap      | ScalarQuery | `FormatMap(operand, mapping)`               | pure   | str.format_map(mapping)           |
| Encode         | ScalarQuery | `Encode(operand, encoding)`                 | pure   | str.encode(encoding) -> bytes     |
| Join           | ScalarQuery | `Join(operand, iterable)`                   | pure   | sep.join(seq)                     |

## Bytes interactions

`forms/primitives/bytes_interactions.py` - all pure (bytes is immutable), every op is a ScalarQuery. Reached via `Bytes` methods.

| Name              | Sort        | Signature                                       | Effect | Meaning                              |
| ----------------- | ----------- | ------------------------------------------------ | ------ | -------------------------------------- |
| Decode            | ScalarQuery | `Decode(operand, encoding)`                       | pure   | bytes.decode(encoding) -> str          |
| Hex               | ScalarQuery | `Hex(operand)`                                    | pure   | bytes.hex()                            |
| BytesUpper        | ScalarQuery | `BytesUpper(operand)`                             | pure   | bytes.upper()                          |
| BytesLower        | ScalarQuery | `BytesLower(operand)`                             | pure   | bytes.lower()                          |
| BytesTitle        | ScalarQuery | `BytesTitle(operand)`                             | pure   | bytes.title()                          |
| BytesCapitalize   | ScalarQuery | `BytesCapitalize(operand)`                        | pure   | bytes.capitalize()                     |
| BytesSwapCase     | ScalarQuery | `BytesSwapCase(operand)`                          | pure   | bytes.swapcase()                       |
| BytesStrip        | ScalarQuery | `BytesStrip(operand, chars)`                      | pure   | bytes.strip(chars)                     |
| BytesLStrip       | ScalarQuery | `BytesLStrip(operand, chars)`                     | pure   | bytes.lstrip(chars)                    |
| BytesRStrip       | ScalarQuery | `BytesRStrip(operand, chars)`                     | pure   | bytes.rstrip(chars)                    |
| BytesSplit        | ScalarQuery | `BytesSplit(operand, sep, maxsplit)`              | pure   | bytes.split(sep, maxsplit)             |
| BytesRSplit       | ScalarQuery | `BytesRSplit(operand, sep, maxsplit)`             | pure   | bytes.rsplit(sep, maxsplit)            |
| BytesSplitLines   | ScalarQuery | `BytesSplitLines(operand, keepends)`              | pure   | bytes.splitlines(keepends)             |
| BytesPartition    | ScalarQuery | `BytesPartition(operand, sep)`                    | pure   | bytes.partition(sep), 3-tuple          |
| BytesRPartition   | ScalarQuery | `BytesRPartition(operand, sep)`                   | pure   | bytes.rpartition(sep), 3-tuple         |
| BytesFind         | ScalarQuery | `BytesFind(operand, sub, start, end)`             | pure   | bytes.find(sub, start, end)            |
| BytesRFind        | ScalarQuery | `BytesRFind(operand, sub, start, end)`            | pure   | bytes.rfind(sub, start, end)           |
| BytesIndex        | ScalarQuery | `BytesIndex(operand, sub, start, end)`            | pure   | bytes.index(sub, start, end), Invalid if absent |
| BytesRIndex       | ScalarQuery | `BytesRIndex(operand, sub, start, end)`           | pure   | bytes.rindex(sub, start, end), Invalid if absent |
| BytesCount        | ScalarQuery | `BytesCount(operand, sub)`                        | pure   | bytes.count(sub)                       |
| BytesStartsWith   | ScalarQuery | `BytesStartsWith(operand, prefix)`                | pure   | bytes.startswith(prefix)               |
| BytesEndsWith     | ScalarQuery | `BytesEndsWith(operand, suffix)`                  | pure   | bytes.endswith(suffix)                 |
| BytesIsAscii      | ScalarQuery | `BytesIsAscii(operand)`                           | pure   | bytes.isascii()                        |
| BytesIsDigit      | ScalarQuery | `BytesIsDigit(operand)`                           | pure   | bytes.isdigit()                        |
| BytesIsAlpha      | ScalarQuery | `BytesIsAlpha(operand)`                           | pure   | bytes.isalpha()                        |
| BytesIsAlnum      | ScalarQuery | `BytesIsAlnum(operand)`                           | pure   | bytes.isalnum()                        |
| BytesIsSpace      | ScalarQuery | `BytesIsSpace(operand)`                           | pure   | bytes.isspace()                        |
| BytesIsTitle      | ScalarQuery | `BytesIsTitle(operand)`                           | pure   | bytes.istitle()                        |
| BytesIsUpper      | ScalarQuery | `BytesIsUpper(operand)`                           | pure   | bytes.isupper()                        |
| BytesIsLower      | ScalarQuery | `BytesIsLower(operand)`                           | pure   | bytes.islower()                        |
| BytesCenter       | ScalarQuery | `BytesCenter(operand, width, fillbyte)`           | pure   | bytes.center(width, fillbyte)          |
| BytesLJust        | ScalarQuery | `BytesLJust(operand, width, fillbyte)`            | pure   | bytes.ljust(width, fillbyte)           |
| BytesRJust        | ScalarQuery | `BytesRJust(operand, width, fillbyte)`            | pure   | bytes.rjust(width, fillbyte)           |
| BytesZFill        | ScalarQuery | `BytesZFill(operand, width)`                      | pure   | bytes.zfill(width)                     |
| BytesExpandTabs   | ScalarQuery | `BytesExpandTabs(operand, tabsize)`               | pure   | bytes.expandtabs(tabsize)              |
| BytesReplace      | ScalarQuery | `BytesReplace(operand, old, new, count)`          | pure   | bytes.replace(old, new, count)         |
| BytesRemovePrefix | ScalarQuery | `BytesRemovePrefix(operand, prefix)`              | pure   | bytes.removeprefix(prefix)             |
| BytesRemoveSuffix | ScalarQuery | `BytesRemoveSuffix(operand, suffix)`              | pure   | bytes.removesuffix(suffix)             |
| BytesTranslate    | ScalarQuery | `BytesTranslate(operand, table, delete)`          | pure   | bytes.translate(table, delete)         |
| BytesJoin         | ScalarQuery | `BytesJoin(operand, iterable)`                    | pure   | sep.join(seq of bytes)                 |

## Collections

`from nu import Dict, DictItems, DictKeys, DictValues, FrozenSet, Iterator, List, Set, Tuple`

| Name       | Sort | Signature              | Effect | Meaning                                                     |
| ---------- | ---- | ----------------------- | ------ | ------------------------------------------------------------ |
| List       | Form | `List[T](source)`       | pure   | mutable sequence interface, comparable                       |
| Tuple      | Form | `Tuple[*Ts](source)`    | pure   | immutable sequence interface, heterogeneous, comparable       |
| Set        | Form | `Set[T](source)`        | pure   | mutable set interface, comparable                             |
| FrozenSet  | Form | `FrozenSet[T](source)`  | pure   | immutable set interface, comparable                           |
| Dict       | Form | `Dict[K, V](source)`    | pure   | mutable mapping interface, comparable                         |
| DictKeys   | Form | `DictKeys[K](source)`   | pure   | set-like key view over a Dict - lazy, live                    |
| DictValues | Form | `DictValues[V](source)` | pure   | collection view over a Dict - iterable, sized, no set ops     |
| DictItems  | Form | `DictItems[K, V](source)` | pure | set-like item view over a Dict - lazy, live                   |
| Iterator   | Form | `Iterator[T](source)`   | pure   | lazy iterator interface - materialize via to_list/to_set/to_tuple |

Constructors (per-Form, exported alongside): `Dict.create()`, `Dict.of(**fields)`, `List.create()`, `Set.create()`, `FrozenSet.create()`, `Tuple.create()`, `Tuple.of(*items)` build the underlying `ScalarQueryFactory` nodes below.

| Name           | Sort        | Signature          | Effect | Meaning                                     |
| -------------- | ----------- | -------------------- | ------ | ---------------------------------------------- |
| DictCreate     | ScalarQuery | `DictCreate()`       | pure   | fresh empty dict                                |
| DictOf         | ScalarQuery | `DictOf(**fields)`   | pure   | dict from named field expressions, `{"a": <x>, ...}` |
| ListCreate     | ScalarQuery | `ListCreate()`       | pure   | fresh empty list                                |
| TupleCreate    | ScalarQuery | `TupleCreate()`      | pure   | fresh empty tuple                               |
| TupleOf        | ScalarQuery | `TupleOf(*items)`    | pure   | tuple from positional item expressions          |
| SetCreate      | ScalarQuery | `SetCreate()`        | pure   | fresh empty set                                 |
| FrozenSetCreate| ScalarQuery | `FrozenSetCreate()`  | pure   | fresh empty frozenset                           |

## Collections abc - Form contracts

`forms/collections/abc/` - abstract bases, not instantiated directly. KEEP the `Form` suffix. Mirror `collections.abc`.

| Name                  | Sort | Signature                                                          | Effect | Meaning                                                              |
| --------------------- | ---- | -------------------------------------------------------------------- | ------ | ----------------------------------------------------------------------- |
| ContainerForm         | Form | `ContainerForm`                                                       | pure   | containment capability - `.contains(item)` -> Bool                     |
| SizedForm             | Form | `SizedForm`                                                           | pure   | length capability - `.len()` -> Int                                    |
| SliceableForm[ResultT]| Form | `SliceableForm[ResultT]`                                              | pure   | slicing capability - `.slice(start, stop, step)`                       |
| IterableForm[ElementT, CollectionResultT, ElementResultT] | Form | `IterableForm[...]`                        | pure   | iteration capability + result-wrapping infra for subclasses            |
| CollectionForm[ElementT, CollectionResultT, ElementResultT] | Form | `CollectionForm[...]`                    | pure   | Sized + Iterable + Container                                           |
| SequenceForm[CollectionT, ElementT, CollectionResultT, ElementResultT] | Form | `SequenceForm[...]`     | pure   | Collection + Sliceable + first/last/index_of/count/reversed_keys        |
| MutableSequenceForm[...]| Form | `MutableSequenceForm[...]`                                          | pure   | Sequence + append/insert/pop/extend/remove/reverse                     |
| ReactiveSequenceForm[...]| Form | `ReactiveSequenceForm[...]`                                        | pure   | MutableSequence + change notifications                                 |
| MappingForm[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT] | Form | `MappingForm[...]`     | pure   | Collection + keys/values/items/get                                     |
| MutableMappingForm[...] | Form | `MutableMappingForm[...]`                                           | pure   | Mapping + set_item/del_item/update/pop/popitem/setdefault/clear         |
| ReactiveMappingForm[...]| Form | `ReactiveMappingForm[...]`                                          | pure   | MutableMapping + change notifications                                  |
| SetLikeForm[CollectionT, ElementT, CollectionResultT, ElementResultT] | Form | `SetLikeForm[...]`       | pure   | Collection + union/intersection/difference/symmetric_difference/subset/superset/disjoint/copy + operators |
| MutableSetForm[...]     | Form | `MutableSetForm[...]`                                               | pure   | SetLike + add/remove/discard/pop/clear/update/*_update + in-place operators |
| ReactiveSetForm[...]    | Form | `ReactiveSetForm[...]`                                              | pure   | MutableSet + change notifications                                      |

## Collections abc - Mapping interactions

`forms/collections/abc/mapping_interactions.py` - reached via `Dict` methods (`.keys()`, `.get()`, ...), not called directly.

| Name        | Sort         | Signature                    | Effect | Meaning                                                     |
| ----------- | ------------ | ------------------------------ | ------ | -------------------------------------------------------------- |
| Keys        | ScalarQuery  | `Keys(mapping)`                 | pure   | mapping.keys()                                                  |
| Values      | ScalarQuery  | `Values(mapping)`               | pure   | mapping.values()                                                |
| Items       | ScalarQuery  | `Items(mapping)`                | pure   | mapping.items()                                                 |
| Get         | ScalarQuery  | `Get(mapping, key, default)`    | pure   | mapping.get(key, default) or mapping[key] when default is None |
| ContainsKey | ScalarQuery  | `ContainsKey(mapping, key)`     | pure   | key in mapping                                                  |
| Copy        | ScalarQuery  | `Copy(mapping)`                 | pure   | shallow copy, new dict                                          |
| ReversedKeys| ScalarQuery  | `ReversedKeys(mapping)`         | pure   | reversed(mapping), keys in reverse insertion order              |
| Merge       | ScalarQuery  | `Merge(mapping, other)`         | pure   | mapping \| other, new dict                                      |
| DeleteItem  | Command      | `DeleteItem(mapping, key)`      | WRITE  | del mapping[key]; mutates slot 0, returns nothing               |
| Update      | Command      | `Update(mapping, other)`        | WRITE  | mapping.update(other); mutates slot 0, returns nothing          |
| MergeUpdate | ScalarAction | `MergeUpdate(mapping, other)`   | WRITE  | mapping \|= other; mutates and yields the mapping                |
| DictPop     | ScalarAction | `DictPop(mapping, key, default)`| WRITE  | mapping.pop(key, default); mutates and yields the popped value  |
| PopItem     | ScalarAction | `PopItem(mapping)`              | WRITE  | mapping.popitem(); mutates and yields the (key, value) pair      |
| SetDefault  | ScalarAction | `SetDefault(mapping, key, default)` | WRITE | mapping.setdefault(key, default); mutates and yields the value |

## Collections abc - Sequence interactions

`forms/collections/abc/sequence_interactions.py` - reached via `List` methods.

| Name        | Sort         | Signature                     | Effect | Meaning                                             |
| ----------- | ------------ | -------------------------------- | ------ | ------------------------------------------------------ |
| First       | ScalarQuery  | `First(seq)`                     | pure   | seq[0], Invalid if empty                                |
| Last        | ScalarQuery  | `Last(seq)`                      | pure   | seq[-1], Invalid if empty                               |
| IndexOf     | ScalarQuery  | `IndexOf(seq, value)`            | pure   | seq.index(value), Invalid if not found                  |
| Count       | ScalarQuery  | `Count(seq, value)`              | pure   | seq.count(value)                                        |
| Copy        | ScalarQuery  | `Copy(seq)`                      | pure   | list.copy(), new list                                   |
| Append      | Command      | `Append(seq, value)`             | WRITE  | seq.append(value); mutates slot 0, returns nothing      |
| Insert      | Command      | `Insert(seq, index, value)`      | WRITE  | seq.insert(index, value); mutates slot 0, returns nothing |
| Extend      | Command      | `Extend(seq, other)`             | WRITE  | seq.extend(other); mutates slot 0, returns nothing      |
| RemoveValue | Command      | `RemoveValue(seq, value)`        | WRITE  | seq.remove(value); mutates slot 0, returns nothing      |
| Reverse     | Command      | `Reverse(seq)`                   | WRITE  | seq.reverse(); mutates slot 0, returns nothing          |
| Sort        | Command      | `Sort(seq)`                      | WRITE  | list.sort(); mutates slot 0, returns nothing (no-key variant only) |
| SetIndex    | Command      | `SetIndex(seq, index, value)`    | WRITE  | seq[index] = value; mutates slot 0, returns nothing     |
| DelIndex    | Command      | `DelIndex(seq, index)`           | WRITE  | del seq[index]; mutates slot 0, returns nothing         |
| Pop         | ScalarAction | `Pop(seq, index)`                | WRITE  | seq.pop(index); mutates and yields the popped value     |
| IAdd        | ScalarAction | `IAdd(seq, other)`               | WRITE  | seq += other; mutates and returns seq                   |
| IMul        | ScalarAction | `IMul(seq, n)`                   | WRITE  | seq *= n; mutates and returns seq                       |

## Collections abc - Set interactions

`forms/collections/abc/set_interactions.py` - reached via `Set` / `FrozenSet` methods.

| Name                     | Sort         | Signature                        | Effect | Meaning                                             |
| ------------------------ | ------------ | ----------------------------------- | ------ | ------------------------------------------------------- |
| Union                    | ScalarQuery  | `Union(left, right)`                | pure   | left.union(right), new set                              |
| Intersection             | ScalarQuery  | `Intersection(left, right)`         | pure   | left.intersection(right), new set                       |
| Difference               | ScalarQuery  | `Difference(left, right)`           | pure   | left.difference(right), new set                         |
| SymmetricDifference      | ScalarQuery  | `SymmetricDifference(left, right)`  | pure   | left.symmetric_difference(right), new set               |
| IsSubset                 | ScalarQuery  | `IsSubset(left, right)`             | pure   | left <= right                                            |
| IsSuperset               | ScalarQuery  | `IsSuperset(left, right)`           | pure   | left >= right                                            |
| IsDisjoint               | ScalarQuery  | `IsDisjoint(left, right)`           | pure   | left.isdisjoint(right)                                   |
| Copy                     | ScalarQuery  | `Copy(s)`                           | pure   | s.copy(), new set                                        |
| SetOr                    | ScalarQuery  | `SetOr(left, right)`                | pure   | left \| right, new set                                   |
| SetAnd                   | ScalarQuery  | `SetAnd(left, right)`               | pure   | left & right, new set                                    |
| SetSub                   | ScalarQuery  | `SetSub(left, right)`               | pure   | left - right, new set                                    |
| SetXor                   | ScalarQuery  | `SetXor(left, right)`               | pure   | left ^ right, new set                                    |
| AddCmd                   | Command      | `AddCmd(s, value)`                  | WRITE  | s.add(value); mutates the set, returns nothing           |
| Remove                   | Command      | `Remove(s, value)`                  | WRITE  | s.remove(value); mutates the set, returns nothing        |
| Discard                  | Command      | `Discard(s, value)`                 | WRITE  | s.discard(value); mutates the set, returns nothing       |
| SetUpdate                | Command      | `SetUpdate(s, other)`               | WRITE  | s.update(other); mutates the set, returns nothing        |
| IntersectionUpdate       | Command      | `IntersectionUpdate(s, other)`      | WRITE  | s.intersection_update(other); mutates the set, returns nothing |
| DifferenceUpdate         | Command      | `DifferenceUpdate(s, other)`        | WRITE  | s.difference_update(other); mutates the set, returns nothing |
| SymmetricDifferenceUpdate| Command      | `SymmetricDifferenceUpdate(s, other)` | WRITE | s.symmetric_difference_update(other); mutates the set, returns nothing |
| SetPop                   | ScalarAction | `SetPop(s)`                         | WRITE  | s.pop(); mutates the set, yields the removed element     |
| SetIOr                   | ScalarAction | `SetIOr(left, right)`               | WRITE  | left \|= right; mutates and returns the set              |
| SetIAnd                  | ScalarAction | `SetIAnd(left, right)`              | WRITE  | left &= right; mutates and returns the set               |
| SetISub                  | ScalarAction | `SetISub(left, right)`              | WRITE  | left -= right; mutates and returns the set               |
| SetIXor                  | ScalarAction | `SetIXor(left, right)`              | WRITE  | left ^= right; mutates and returns the set               |

## Collections abc - Shared interactions

`forms/collections/abc/shared_interactions.py` - shared across mutable collections.

| Name  | Sort    | Signature          | Effect | Meaning                                             |
| ----- | ------- | -------------------- | ------ | ------------------------------------------------------ |
| Clear | Command | `Clear(collection)`  | WRITE  | collection.clear(); mutates the collection, returns nothing |
