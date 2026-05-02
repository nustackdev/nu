# Query

Value-producing atoms. READ-only effects (pure unless a child reads). Sub-shapes: ScalarQuery, StreamQuery, Reduction (Scalar with stream child), Literal (trivial Scalar).

Core only - shapes and ext/ not included.

## Literal

| Name    | Sub-shape   | Signature        | Effect | Meaning                              |
| ------- | ----------- | ---------------- | ------ | ------------------------------------ |
| Literal | ScalarQuery | `Literal(value)` | pure   | pure leaf - holds and yields a value |

## Comparison

| Name   | Sub-shape   | Signature         | Effect | Meaning                     |
| ------ | ----------- | ----------------- | ------ | --------------------------- |
| Eq     | ScalarQuery | `Eq(left, right)` | pure   | left == right (commutative) |
| Ne     | ScalarQuery | `Ne(left, right)` | pure   | left != right (commutative) |
| Gt     | ScalarQuery | `Gt(left, right)` | pure   | left > right                |
| Lt     | ScalarQuery | `Lt(left, right)` | pure   | left < right                |
| Ge     | ScalarQuery | `Ge(left, right)` | pure   | left >= right               |
| Le     | ScalarQuery | `Le(left, right)` | pure   | left <= right               |
| IdComp | ScalarQuery | `IdComp(a, b)`    | pure   | identity comparison (`is`)  |

## Logical

| Name | Sub-shape   | Signature        | Effect | Meaning                   |
| ---- | ----------- | ---------------- | ------ | ------------------------- |
| Not  | ScalarQuery | `Not(operand)`   | pure   | logical NOT               |
| Bool | ScalarQuery | `Bool(operand)`  | pure   | bool(operand)             |
| And  | ScalarQuery | `And(left, right)` | pure | short-circuit conjunction |
| Or   | ScalarQuery | `Or(left, right)`  | pure | short-circuit disjunction |

## Arithmetic

| Name     | Sub-shape   | Signature              | Effect | Meaning                |
| -------- | ----------- | ---------------------- | ------ | ---------------------- |
| Neg      | ScalarQuery | `Neg(operand)`         | pure   | -operand               |
| Pos      | ScalarQuery | `Pos(operand)`         | pure   | +operand               |
| Abs      | ScalarQuery | `Abs(operand)`         | pure   | abs(operand)           |
| Add      | ScalarQuery | `Add(left, right)`     | pure   | left + right           |
| Sub      | ScalarQuery | `Sub(left, right)`     | pure   | left - right           |
| Mul      | ScalarQuery | `Mul(left, right)`     | pure   | left * right           |
| Div      | ScalarQuery | `Div(left, right)`     | pure   | left / right           |
| FloorDiv | ScalarQuery | `FloorDiv(left, right)`| pure   | left // right          |
| Mod      | ScalarQuery | `Mod(left, right)`     | pure   | left % right           |
| Pow      | ScalarQuery | `Pow(left, right)`     | pure   | left ** right          |

## Bitwise

| Name       | Sub-shape   | Signature                | Effect | Meaning        |
| ---------- | ----------- | ------------------------ | ------ | -------------- |
| BitwiseNot | ScalarQuery | `BitwiseNot(operand)`    | pure   | ~operand       |
| BitwiseAnd | ScalarQuery | `BitwiseAnd(left, right)`| pure   | left & right   |
| BitwiseOr  | ScalarQuery | `BitwiseOr(left, right)` | pure   | left \| right  |
| Xor        | ScalarQuery | `Xor(left, right)`       | pure   | left ^ right   |
| LShift     | ScalarQuery | `LShift(left, right)`    | pure   | left << right  |
| RShift     | ScalarQuery | `RShift(left, right)`    | pure   | left >> right  |

## Conversion

| Name    | Sub-shape   | Signature                  | Effect | Meaning             |
| ------- | ----------- | -------------------------- | ------ | ------------------- |
| ToInt   | ScalarQuery | `ToInt(operand)`           | pure   | int(operand)        |
| ToFloat | ScalarQuery | `ToFloat(operand)`         | pure   | float(operand)      |
| ToBool  | ScalarQuery | `ToBool(operand)`          | pure   | bool(operand)       |
| ToStr   | ScalarQuery | `ToStr(operand)`           | pure   | str(operand)        |
| ToBytes | ScalarQuery | `ToBytes(operand, encoding)`| pure  | bytes(operand)      |
| ToList  | ScalarQuery | `ToList(operand)`          | pure   | list(operand)       |
| ToSet   | ScalarQuery | `ToSet(operand)`           | pure   | set(operand)        |
| ToTuple | ScalarQuery | `ToTuple(operand)`         | pure   | tuple(operand)      |

## Sentinel

| Name       | Sub-shape   | Signature             | Effect | Meaning                        |
| ---------- | ----------- | --------------------- | ------ | ------------------------------ |
| IsEmpty    | ScalarQuery | `IsEmpty(operand)`    | pure   | operand is EMPTY               |
| NotEmpty   | ScalarQuery | `NotEmpty(operand)`   | pure   | operand is not EMPTY           |
| IsInvalid  | ScalarQuery | `IsInvalid(operand)`  | pure   | operand is INVALID             |
| NotInvalid | ScalarQuery | `NotInvalid(operand)` | pure   | operand is not INVALID         |

## Access

| Name     | Sub-shape   | Signature                          | Effect | Meaning                        |
| -------- | ----------- | ---------------------------------- | ------ | ------------------------------ |
| Len      | ScalarQuery | `Len(operand)`                     | pure   | len(operand)                   |
| At       | ScalarQuery | `At(left, right)`                  | pure   | left[right]                    |
| Slice    | ScalarQuery | `Slice(operand, start, stop, step)`| pure   | operand[start:stop:step]       |
| Contains | ScalarQuery | `Contains(left, right)`            | pure   | right in left                  |

## Attr

| Name    | Sub-shape   | Signature                            | Effect | Meaning              |
| ------- | ----------- | ------------------------------------ | ------ | -------------------- |
| GetAttr | ScalarQuery | `GetAttr(instance, attr_name)`       | pure   | getattr              |
| SetAttr | ScalarQuery | `SetAttr(instance, attr_name, value)`| pure   | setattr              |
| DelAttr | ScalarQuery | `DelAttr(instance, attr_name)`       | pure   | delattr              |

## Slice

| Name | Sub-shape   | Signature           | Effect | Meaning              |
| ---- | ----------- | ------------------- | ------ | -------------------- |
| Take | ScalarQuery | `Take(iterable, n)` | pure   | first n elements     |
| Drop | ScalarQuery | `Drop(iterable, n)` | pure   | drop first n elements|

## Combine

| Name      | Sub-shape   | Signature                     | Effect | Meaning                  |
| --------- | ----------- | ----------------------------- | ------ | ------------------------ |
| Zip       | ScalarQuery | `Zip(*operands)`              | pure   | zip iterables            |
| Chain     | ScalarQuery | `Chain(*operands)`            | pure   | chain iterables          |
| Enumerate | ScalarQuery | `Enumerate(iterable, start)`  | pure   | enumerate with start     |

## Transform

| Name     | Sub-shape   | Signature                        | Effect | Meaning                       |
| -------- | ----------- | -------------------------------- | ------ | ----------------------------- |
| Sorted   | ScalarQuery | `Sorted(iterable, reverse)`      | pure   | sorted list                   |
| Reversed | ScalarQuery | `Reversed(operand)`              | pure   | reversed iterator             |
| Pluck    | ScalarQuery | `Pluck(iterable, key)`           | pure   | extract field per element     |
| FilterBy | ScalarQuery | `FilterBy(iterable, field, value)`| pure  | filter by field equality      |
| Flatten  | ScalarQuery | `Flatten(operand)`               | pure   | flatten one level             |
| Unique   | ScalarQuery | `Unique(operand)`                | pure   | unique elements, order kept   |

## Reduce

| Name    | Sub-shape   | Signature        | Effect | Meaning             |
| ------- | ----------- | ---------------- | ------ | ------------------- |
| Sum     | ScalarQuery | `Sum(operand)`   | pure   | sum of elements     |
| MinElem | ScalarQuery | `MinElem(operand)`| pure  | minimum element     |
| MaxElem | ScalarQuery | `MaxElem(operand)`| pure  | maximum element     |
| AnyElem | ScalarQuery | `AnyElem(operand)`| pure  | any truthy element  |
| AllElem | ScalarQuery | `AllElem(operand)`| pure  | all truthy          |

## Reduction (Scalar with stream child)

| Name    | Sub-shape | Signature                       | Effect | Meaning                          |
| ------- | --------- | ------------------------------- | ------ | -------------------------------- |
| First   | Reduction | `First(stream)`                 | pure   | first yield, or EMPTY            |
| Last    | Reduction | `Last(stream)`                  | pure   | last yield, or EMPTY             |
| Collect | Reduction | `Collect(stream)`               | pure   | drain stream into a list         |
| Reduce  | Reduction | `Reduce(stream, fn, initial)`   | pure   | fold with a Python callable      |

## Iter-reduce (stream-shaped reductions)

| Name      | Sub-shape | Signature                              | Effect | Meaning                                     |
| --------- | --------- | -------------------------------------- | ------ | ------------------------------------------- |
| Find      | Reduction | `Find(items, condition, item)`         | pure   | first item where condition holds, else None |
| FindIndex | Reduction | `FindIndex(items, condition, item)`    | pure   | index of first match, -1 if none            |
| GroupBy   | Reduction | `GroupBy(items, key, item)`            | pure   | `{key: [items]}` grouped by key             |
| Partition | Reduction | `Partition(items, condition, item)`    | pure   | `(matches, rest)` split by condition        |
| ToDict    | Reduction | `ToDict(items, key, value, item)`      | pure   | dict from key/value over each item          |

## Stream

### Source

| Name | Sub-shape   | Signature      | Effect | Meaning                            |
| ---- | ----------- | -------------- | ------ | ---------------------------------- |
| Iter | StreamQuery | `Iter(source)` | pure   | open a scalar iterable as a stream |

### Transform

| Name      | Sub-shape   | Signature                       | Effect | Meaning                              |
| --------- | ----------- | ------------------------------- | ------ | ------------------------------------ |
| Map       | StreamQuery | `Map(items, transform, item)`   | pure   | yield transform(item) per element    |
| Filter    | StreamQuery | `Filter(items, condition, item)`| pure   | yield items where condition is true  |
| TakeWhile | StreamQuery | `TakeWhile(items, condition, item)`| pure| yield while condition holds          |
| UniqueDo  | StreamQuery | `UniqueDo(items, key, item)`    | pure   | yield items with unseen key          |

### Fold

| Name | Sub-shape   | Signature                              | Effect | Meaning                                    |
| ---- | ----------- | -------------------------------------- | ------ | ------------------------------------------ |
| Fold | StreamQuery | `Fold(items, acc, initial, item, body)`| pure   | stateful sequential reduction over a stream |

## Control

| Name   | Sub-shape   | Signature                                  | Effect | Meaning                                  |
| ------ | ----------- | ------------------------------------------ | ------ | ---------------------------------------- |
| If     | ScalarQuery | `If(condition, then_branch, else_branch)`  | pure   | conditional Query                        |
| Switch | ScalarQuery | `Switch(selector, cases, default)`         | pure   | multi-way Query branch on selector value |

## Timing

| Name  | Sub-shape   | Signature           | Effect | Meaning                              |
| ----- | ----------- | ------------------- | ------ | ------------------------------------ |
| Timed | ScalarQuery | `Timed(body, label)`| pure   | run body, return wall-clock duration |
