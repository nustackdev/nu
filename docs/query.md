# Query

Value-producing atoms. READ-only effects. Sub-shapes: ScalarQuery, StreamQuery, Reduction (Scalar with stream child), Literal (trivial Scalar).

Partial - samples below to confirm direction.

## Comparison

| Name    | Sub-shape   | Signature           | Effect | Meaning                       |
| ------- | ----------- | ------------------- | ------ | ----------------------------- |
| Eq      | ScalarQuery | `Eq(left, right)`   | pure   | left == right (commutative)   |
| Ne      | ScalarQuery | `Ne(left, right)`   | pure   | left != right (commutative)   |
| Gt      | ScalarQuery | `Gt(left, right)`   | pure   | left > right                  |
| Lt      | ScalarQuery | `Lt(left, right)`   | pure   | left < right                  |
| Ge      | ScalarQuery | `Ge(left, right)`   | pure   | left >= right                 |
| Le      | ScalarQuery | `Le(left, right)`   | pure   | left <= right                 |
| IdComp  | ScalarQuery | `IdComp(a, b)`      | pure   | identity comparison (`is`)    |

## Logical

| Name | Sub-shape   | Signature   | Effect | Meaning                  |
| ---- | ----------- | ----------- | ------ | ------------------------ |
| Not  | ScalarQuery | `Not(x)`    | pure   | logical negation         |
| Bool | ScalarQuery | `Bool(x)`   | pure   | truthiness coercion      |
| And  | ScalarQuery | `And(*xs)`  | pure   | short-circuit conjunction |
| Or   | ScalarQuery | `Or(*xs)`   | pure   | short-circuit disjunction |

## Stream transform

| Name      | Sub-shape   | Signature              | Effect | Meaning                          |
| --------- | ----------- | ---------------------- | ------ | -------------------------------- |
| Iter      | StreamQuery | `Iter(source)`         | pure   | open a source as a stream        |
| Map       | StreamQuery | `Map(stream, f)`       | pure   | apply f to each element          |
| Filter    | StreamQuery | `Filter(stream, pred)` | pure   | keep elements where pred is true |
| TakeWhile | StreamQuery | `TakeWhile(stream, p)` | pure   | take while predicate holds       |
| UniqueDo  | StreamQuery | `UniqueDo(stream)`     | pure   | drop duplicates as they pass     |

## Reduction

| Name    | Sub-shape | Signature              | Effect | Meaning                    |
| ------- | --------- | ---------------------- | ------ | -------------------------- |
| First   | Reduction | `First(stream)`        | pure   | first element or EMPTY     |
| Last    | Reduction | `Last(stream)`         | pure   | last element or EMPTY      |
| Collect | Reduction | `Collect(stream)`      | pure   | materialize into a list    |
| Reduce  | Reduction | `Reduce(stream, f, z)` | pure   | fold with f from initial z |

> Remaining sections pending: arithmetic, bitwise, access, attr, control (`If`/`Switch`), conversion, slice, combine, sentinel, timing.
