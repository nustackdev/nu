---
title: nu.core
---

Atom interactions on host values: arithmetic, logical, comparison, cast, reduction, transform, iteration, access, reflection, repr, sentinel, conditional, dynamic, reactive, io, bitwise, literal. One group per source file in `nu/core/`.

`from nu import Add` (flat-exported); dotted equivalent `from nu.core.arithmetic import Add`.

## Literal

`from nu import Literal`

| Name    | Sort        | Signature        | Effect | Meaning                              |
| ------- | ----------- | ----------------- | ------ | ------------------------------------ |
| Literal | ScalarQuery | `Literal(value)`  | pure   | constant leaf - holds and yields a value |

## Arithmetic

`from nu import Add, Sub, Mul, MatMul, Div, FloorDiv, Mod, Pow, Neg, Pos, Abs, DivMod, Round`

| Name     | Sort        | Signature                  | Effect | Meaning                                    |
| -------- | ----------- | --------------------------- | ------ | ------------------------------------------ |
| Add      | ScalarQuery | `Add(*operands)`            | pure   | sum of children (commutative, associative, variadic) |
| Sub      | ScalarQuery | `Sub(left, right)`          | pure   | left - right                                |
| Mul      | ScalarQuery | `Mul(*operands)`            | pure   | product of children (commutative, associative, variadic) |
| MatMul   | ScalarQuery | `MatMul(left, right)`       | pure   | left @ right                                |
| Div      | ScalarQuery | `Div(left, right)`          | pure   | left / right (true division)                |
| FloorDiv | ScalarQuery | `FloorDiv(left, right)`     | pure   | left // right                               |
| Mod      | ScalarQuery | `Mod(left, right)`          | pure   | left % right                                |
| Pow      | ScalarQuery | `Pow(left, right)`          | pure   | left ** right                               |
| Neg      | ScalarQuery | `Neg(operand)`              | pure   | -operand                                    |
| Pos      | ScalarQuery | `Pos(operand)`              | pure   | +operand                                    |
| Abs      | ScalarQuery | `Abs(operand)`              | pure   | abs(operand)                                |
| DivMod   | ScalarQuery | `DivMod(left, right)`       | pure   | (quotient, remainder) pair                  |
| Round    | ScalarQuery | `Round(value, ndigits=None)`| pure   | round(value[, ndigits])                     |

## Bitwise

`from nu import BitAnd, BitOr, BitXor, BitNot, LShift, RShift`

| Name   | Sort        | Signature               | Effect | Meaning                                    |
| ------ | ----------- | ------------------------ | ------ | ------------------------------------------ |
| BitAnd | ScalarQuery | `BitAnd(*operands)`      | pure   | bitwise AND of children (commutative, associative, variadic) |
| BitOr  | ScalarQuery | `BitOr(*operands)`       | pure   | bitwise OR of children (commutative, associative, variadic)  |
| BitXor | ScalarQuery | `BitXor(*operands)`      | pure   | bitwise XOR of children (commutative, associative, variadic) |
| BitNot | ScalarQuery | `BitNot(operand)`        | pure   | ~operand                                   |
| LShift | ScalarQuery | `LShift(left, right)`    | pure   | left << right                              |
| RShift | ScalarQuery | `RShift(left, right)`    | pure   | left >> right                              |

## Cast

`from nu import ToInt, ToFloat, ToComplex, ToStr, ToBytes, ToByteArray, ToList, ToTuple, ToSet, ToFrozenSet, ToDict`

Scalar casts are evaluable now; the collection constructors are declared structural stubs pending the stream/fabric runtime. `ToBool` (truthiness) lives in `logical`, not here.

| Name        | Sort        | Signature                         | Effect | Meaning                              |
| ----------- | ----------- | ---------------------------------- | ------ | ------------------------------------- |
| ToInt       | ScalarQuery | `ToInt(value, base=None)`          | pure   | int(value[, base])                    |
| ToFloat     | ScalarQuery | `ToFloat(operand)`                 | pure   | float(operand)                        |
| ToComplex   | ScalarQuery | `ToComplex(real, imag=None)`       | pure   | complex(real[, imag])                 |
| ToStr       | ScalarQuery | `ToStr(operand)`                   | pure   | str(operand)                          |
| ToBytes     | ScalarQuery | `ToBytes(value, encoding=None)`    | pure   | bytes(value[, encoding])              |
| ToByteArray | ScalarQuery | `ToByteArray(value, encoding=None)`| pure   | bytearray(value[, encoding])          |
| ToList      | ScalarQuery | `ToList(iterable)`                 | pure   | list(iterable) - structural stub      |
| ToTuple     | ScalarQuery | `ToTuple(iterable)`                | pure   | tuple(iterable) - structural stub     |
| ToSet       | ScalarQuery | `ToSet(iterable)`                  | pure   | set(iterable) - structural stub       |
| ToFrozenSet | ScalarQuery | `ToFrozenSet(iterable)`            | pure   | frozenset(iterable) - structural stub |
| ToDict      | ScalarQuery | `ToDict(pairs)`                    | pure   | dict(pairs) - structural stub         |

## Comparison

`from nu import Eq, Ne, Lt, Gt, Le, Ge, Is`

| Name | Sort        | Signature         | Effect | Meaning                     |
| ---- | ----------- | ------------------ | ------ | ---------------------------- |
| Eq   | ScalarQuery | `Eq(left, right)`  | pure   | left == right (commutative) |
| Ne   | ScalarQuery | `Ne(left, right)`  | pure   | left != right (commutative) |
| Lt   | ScalarQuery | `Lt(left, right)`  | pure   | left < right                 |
| Gt   | ScalarQuery | `Gt(left, right)`  | pure   | left > right                 |
| Le   | ScalarQuery | `Le(left, right)`  | pure   | left <= right                |
| Ge   | ScalarQuery | `Ge(left, right)`  | pure   | left >= right                |
| Is   | ScalarQuery | `Is(left, right)`  | pure   | left is right (commutative)  |

## Conditional

`from nu import If, Switch`

Value-yielding branch selection - the Query siblings to the mutating `IfDo` / `SwitchDo` in `nu.flows.control`.

| Name   | Sort        | Signature                              | Effect | Meaning                                        |
| ------ | ----------- | ---------------------------------------- | ------ | ----------------------------------------------- |
| If     | ScalarQuery | `If(cond, then, else_)`                  | pure   | yield then if cond truthy, else else_ (short-circuits) |
| Switch | ScalarQuery | `Switch(selector, cases, default=None)`  | pure   | yield the value keyed by matching selector, else default |

## Dynamic

`from nu import Eval, Compile, Globals, Locals, Exec`

`Eval` / `Compile` fold purely over operand values. `Globals` / `Locals` / `Exec` are escape hatches into the live host interpreter namespace, bypassing the Context entirely.

| Name    | Sort        | Signature                             | Effect | Meaning                                        |
| ------- | ----------- | --------------------------------------- | ------ | ----------------------------------------------- |
| Eval    | ScalarQuery | `Eval(source, globals=None, locals=None)` | pure | eval(source[, globals, locals])                 |
| Compile | ScalarQuery | `Compile(source, filename, mode)`       | pure   | compile(source, filename, mode) -> code object  |
| Globals | ScalarQuery | `Globals()`                             | pure   | escape hatch: live host globals() dict           |
| Locals  | ScalarQuery | `Locals()`                              | pure   | escape hatch: live host locals() dict            |
| Exec    | ScalarQuery | `Exec(namespace, source)`               | pure   | escape hatch: exec(source, namespace), yields namespace |

## Logical

`from nu import And, Or, Not, ToBool`

Nu's `And` / `Or` do not short-circuit like Python's - they coerce every operand to bool and fold eagerly, always yielding a plain bool.

| Name   | Sort        | Signature         | Effect | Meaning                                          |
| ------ | ----------- | ------------------ | ------ | -------------------------------------------------- |
| And    | ScalarQuery | `And(*operands)`  | pure   | conjunction of children, eager (commutative, associative, idempotent); True if empty |
| Or     | ScalarQuery | `Or(*operands)`   | pure   | disjunction of children, eager (commutative, associative, idempotent); False if empty |
| Not    | ScalarQuery | `Not(operand)`    | pure   | logical negation                                    |
| ToBool | ScalarQuery | `ToBool(operand)` | pure   | bool(operand) truthiness                            |

## Reduction

`from nu import Sum, Min, Max, AnyOf, AllOf, Count, First, Last, Collect`

Scalar-over-stream folds - the Reduction sub-shape bridging a stream child down to one scalar.

| Name  | Sort      | Signature       | Effect | Meaning                                                    |
| ----- | --------- | ---------------- | ------ | ------------------------------------------------------------ |
| Sum   | Reduction | `Sum(stream)`    | pure   | sum of items (commutative, associative)                     |
| Min   | Reduction | `Min(stream)`    | pure   | smallest item (commutative, associative, idempotent); EMPTY if empty |
| Max   | Reduction | `Max(stream)`    | pure   | largest item (commutative, associative, idempotent); EMPTY if empty  |
| AnyOf | Reduction | `AnyOf(stream)`  | pure   | true if any item truthy (commutative, associative, idempotent) |
| AllOf | Reduction | `AllOf(stream)`  | pure   | true if every item truthy (commutative, associative, idempotent) |
| Count | Reduction | `Count(stream)`  | pure   | number of items (commutative, associative)                   |
| First | Reduction | `First(stream)`  | pure   | first item; EMPTY if empty                                   |
| Last  | Reduction | `Last(stream)`   | pure   | last item; EMPTY if empty                                    |
| Collect | Reduction | `Collect(stream)` | pure | drain stream into a list                                     |

## Transform

`from nu import Map, Filter, Sorted, SortBy, Flatten, Unique`

Stream-to-stream lazy lenses; `Sorted` and `SortBy` are eager (drain the source first). `Map` / `Filter` / `SortBy` bind each item into the attrs side-channel under a name child, read back in the body via `AttrRef(<name>)`.

| Name    | Sort        | Signature                                         | Effect | Meaning                                             |
| ------- | ----------- | --------------------------------------------------- | ------ | ----------------------------------------------------- |
| Map     | StreamQuery | `Map(source, transform, key="item")`                | pure   | yield transform(item) per element, lazy                |
| Filter  | StreamQuery | `Filter(source, predicate, key="item")`             | pure   | yield items where predicate holds, lazy                |
| Sorted  | StreamQuery | `Sorted(source)`                                    | pure   | source ordered, eager (drains then sorts)               |
| SortBy  | StreamQuery | `SortBy(source, key, reverse=False, item="item")`   | pure   | source ordered by per-item key expr, eager              |
| Flatten | StreamQuery | `Flatten(source)`                                   | pure   | one-level concat of iterable-of-iterables, lazy         |
| Unique  | StreamQuery | `Unique(source)`                                    | pure   | first-seen-order dedupe, lazy (items must be hashable)  |

## Iteration

`from nu import Iter, Enumerate, Next, Zip, Reversed`

Iterator sources are StreamQuery; `Next` steps a ref-held iterator (mutate-and-yield) so it is the first concrete Action in core.

| Name      | Sort         | Signature                        | Effect | Meaning                                          |
| --------- | ------------ | ---------------------------------- | ------ | --------------------------------------------------- |
| Iter      | StreamQuery  | `Iter(source)`                    | pure   | lift a scalar iterable child into a stream           |
| Enumerate | StreamQuery  | `Enumerate(source, start=0)`      | pure   | (index, item) pairs, index from start                |
| Zip       | StreamQuery  | `Zip(*sources)`                   | pure   | thread sources item by item, stop at shortest         |
| Reversed  | StreamQuery  | `Reversed(source)`                | pure   | source items in reverse order                        |
| Next      | ScalarAction | `Next(iterator)`                  | mutate + yield | advance a ref-held iterator, yield the item   |

## Access

`from nu import GetItem, Len, Contains, Slice, GetAttr, HasAttr, SetItem, DelItem, SetAttr, DelAttr`

Reads are ScalarQuery; writes are Command (local Python mutation, not a fabric write - `context.Set` / `context.Delete` own fabric writes).

| Name    | Sort        | Signature                                | Effect  | Meaning                                  |
| ------- | ----------- | ------------------------------------------ | ------- | ------------------------------------------ |
| GetItem | ScalarQuery | `GetItem(target, key)`                    | pure    | target[key]                                 |
| Len     | ScalarQuery | `Len(operand)`                             | pure    | len(operand)                                |
| Contains| ScalarQuery | `Contains(container, item)`               | pure    | item in container                           |
| Slice   | ScalarQuery | `Slice(start, stop, step)`                | pure    | slice(start, stop, step)                    |
| GetAttr | ScalarQuery | `GetAttr(obj, name, default=None)`        | pure    | getattr(obj, name[, default])               |
| HasAttr | ScalarQuery | `HasAttr(obj, name)`                      | pure    | hasattr(obj, name)                          |
| SetItem | Command     | `SetItem(target, key, value)`             | mutates target | target[key] = value                 |
| DelItem | Command     | `DelItem(target, key)`                    | mutates target | del target[key]                     |
| SetAttr | Command     | `SetAttr(obj, name, value)`               | mutates obj     | setattr(obj, name, value)           |
| DelAttr | Command     | `DelAttr(obj, name)`                      | mutates obj     | delattr(obj, name)                  |

## Reflection

`from nu import Type, IsInstance, IsSubclass, Callable, Id, Hash, Dir, Vars`

| Name       | Sort        | Signature                     | Effect | Meaning                          |
| ---------- | ----------- | -------------------------------- | ------ | ----------------------------------- |
| Type       | ScalarQuery | `Type(operand)`                 | pure   | type(operand)                       |
| IsInstance | ScalarQuery | `IsInstance(value, klass)`      | pure   | isinstance(value, klass)            |
| IsSubclass | ScalarQuery | `IsSubclass(cls, klass)`        | pure   | issubclass(cls, klass)              |
| Callable   | ScalarQuery | `Callable(operand)`             | pure   | callable(operand)                   |
| Id         | ScalarQuery | `Id(operand)`                   | pure   | id(operand)                         |
| Hash       | ScalarQuery | `Hash(operand)`                 | pure   | hash(operand)                       |
| Dir        | ScalarQuery | `Dir(operand)`                  | pure   | dir(operand)                        |
| Vars       | ScalarQuery | `Vars(operand)`                 | pure   | vars(operand) - the __dict__        |

## Repr

`from nu import Repr, Ascii, Format, Bin, Hex, Oct, Ord, Chr`

| Name   | Sort        | Signature                  | Effect | Meaning                          |
| ------ | ----------- | ---------------------------- | ------ | ----------------------------------- |
| Repr   | ScalarQuery | `Repr(operand)`             | pure   | repr(operand)                       |
| Ascii  | ScalarQuery | `Ascii(operand)`            | pure   | ascii(operand)                      |
| Format | ScalarQuery | `Format(value, spec=None)`  | pure   | format(value[, spec])               |
| Bin    | ScalarQuery | `Bin(operand)`              | pure   | bin(operand)                        |
| Hex    | ScalarQuery | `Hex(operand)`              | pure   | hex(operand)                        |
| Oct    | ScalarQuery | `Oct(operand)`              | pure   | oct(operand)                        |
| Ord    | ScalarQuery | `Ord(operand)`              | pure   | ord(operand)                        |
| Chr    | ScalarQuery | `Chr(operand)`              | pure   | chr(operand)                        |

## Sentinel

`from nu import IsEmpty, NotEmpty, IsInvalid, NotInvalid`

The one core family that observes sentinels rather than propagating them - no EMPTY / INVALID short-circuit in the compile thunk.

| Name       | Sort        | Signature             | Effect | Meaning                 |
| ---------- | ----------- | ------------------------ | ------ | -------------------------- |
| IsEmpty    | ScalarQuery | `IsEmpty(operand)`      | pure   | operand is EMPTY            |
| NotEmpty   | ScalarQuery | `NotEmpty(operand)`     | pure   | operand is not EMPTY        |
| IsInvalid  | ScalarQuery | `IsInvalid(operand)`    | pure   | operand is INVALID          |
| NotInvalid | ScalarQuery | `NotInvalid(operand)`   | pure   | operand is not INVALID      |

## Reactive

`from nu import OnChange, OnChildChange, OnChildrenChange, OnDescendantsChange, OnPrimitiveChange`

Change subscriptions against the process-scope `ObserverProtocol`. Async-only - the sync compile path raises `RuntimeError`, use `nu.arun`.

| Name                | Sort        | Signature                                       | Effect | Meaning                                                  |
| -------------------- | ----------- | -------------------------------------------------- | ------ | ----------------------------------------------------------- |
| OnChange             | ScalarQuery | `OnChange(ref)`                                    | pure (async) | subscribe to any change on the ref's view                |
| OnChildChange        | ScalarQuery | `OnChildChange(ref, address)`                      | pure (async) | subscribe to changes on one specific child                |
| OnChildrenChange     | ScalarQuery | `OnChildrenChange(ref)`                            | pure (async) | subscribe to changes on all immediate children             |
| OnDescendantsChange  | ScalarQuery | `OnDescendantsChange(ref, *pattern)`               | pure (async) | subscribe to descendants matching a pattern                 |
| OnPrimitiveChange    | ScalarQuery | `OnPrimitiveChange(ref)`                           | pure (async) | subscribe on a leaf ref's parent view, keyed by its address |

## IO

`from nu.core.io import Print, Input, print, input, StdioRef, StdioBackend, STDOUT, STDERR, STDIN`

Console read/write through the stdio fabric - not flat-exported at `nu.*`. Both go through a `StdioRef` (`STDOUT`/`STDERR`/`STDIN`) so effect synthesis keeps console IO serial. Prefer the lowercase wrapper functions `print()` / `input()`; they inject the Ref for you.

| Name  | Sort         | Signature                                                   | Effect              | Meaning                                    |
| ----- | ------------ | -------------------------------------------------------------- | -------------------- | --------------------------------------------- |
| Print | Command      | `Print(ref, *values, sep=" ", end="\n", flush=False)`          | mutates stdio fabric | write values to a stream, Python's print       |
| Input | ScalarAction | `Input(ref)`                                                    | mutates + yields stdio fabric | read one line from stdin, newline stripped |
