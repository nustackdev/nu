---
title: nu.mem
---

In-process fabric adapter: plain nested Python dicts as the data bag. No
storage backend, no views, no reactivity — just dicts. Concrete Ref
implementations for the shape Ref blueprints (`nu.shape.refs`), plus a
janus-backed queue ref for bridging asyncio and threads.

## Base

`from nu.mem import RefBase`

| Name    | Sort  | Signature                                             | Effect     | Meaning                                                              |
| ------- | ----- | ------------------------------------------------------ | ---------- | --------------------------------------------------------------------- |
| RefBase | class | `RefBase(address, *, parent_ref=None, owner_shape=None)` | read/write | dict-substrate base: resolves the on-tree parent chain at runtime, no backend |

## Items

`from nu.mem import ItemRef, IntRef, StrRef, FloatRef, BoolRef, BytesRef`

| Name     | Sort  | Signature                                                        | Effect     | Meaning                                                    |
| -------- | ----- | ------------------------------------------------------------------ | ---------- | ------------------------------------------------------------ |
| ItemRef  | class | `ItemRef(address, *, value_type, value_value_type, parent_ref=None, owner_shape=None)` | read/write | generic typed value holder in a nested dict slot              |
| IntRef   | class | `IntRef(address, *, parent_ref=None, owner_shape=None)`             | read/write | dict integer ref with full numeric interface (`Int` mixin); adds `inc`/`dec` |
| StrRef   | class | `StrRef(address, *, parent_ref=None, owner_shape=None)`             | read/write | dict string ref with full string interface (`Str` mixin)      |
| FloatRef | class | `FloatRef(address, *, parent_ref=None, owner_shape=None)`           | read/write | dict float ref with full numeric interface (`Float` mixin)    |
| BoolRef  | class | `BoolRef(address, *, parent_ref=None, owner_shape=None)`            | read/write | dict boolean ref with full logical interface (`Bool` mixin)   |
| BytesRef | class | `BytesRef(address, *, parent_ref=None, owner_shape=None)`           | read/write | dict bytes ref with full bytes interface (`Bytes` mixin)      |

## Dict

`from nu.mem import DictRef`

| Name    | Sort  | Signature                                                                                  | Effect     | Meaning                                    |
| ------- | ----- | --------------------------------------------------------------------------------------------- | ---------- | --------------------------------------------- |
| DictRef | class | `DictRef(address, *, value_type, key_type, key_value_type, value_value_type, parent_ref=None, owner_shape=None)` | read/write | key-value mapping container backed by a nested dict |

## Dict Shapes

`from nu.mem import ShapesDictRef`

| Name          | Sort  | Signature                                                                          | Effect     | Meaning                                     |
| ------------- | ----- | ------------------------------------------------------------------------------------- | ---------- | ----------------------------------------------- |
| ShapesDictRef | class | `ShapesDictRef(address, *, shape_type, key_type, key_value_type, parent_ref=None, owner_shape=None)` | read/write | mapping of homogeneous shapes; key descent yields a `ShapeRef` |

## List

`from nu.mem import ListRef`

| Name    | Sort  | Signature                                                                | Effect     | Meaning                                    |
| ------- | ----- | --------------------------------------------------------------------------- | ---------- | --------------------------------------------- |
| ListRef | class | `ListRef(address, *, item_type, item_value_type, parent_ref=None, owner_shape=None)` | read/write | ordered element container backed by a nested list |

## List Shapes

`from nu.mem import ShapesListRef`

| Name          | Sort  | Signature                                                       | Effect     | Meaning                                     |
| ------------- | ----- | -------------------------------------------------------------------- | ---------- | ----------------------------------------------- |
| ShapesListRef | class | `ShapesListRef(address, *, shape_type, parent_ref=None, owner_shape=None)` | read/write | sequence of homogeneous shapes; index descent yields a `ShapeRef` |

## Set

`from nu.mem import SetRef`

| Name   | Sort  | Signature                                                       | Effect     | Meaning                                  |
| ------ | ----- | -------------------------------------------------------------------- | ---------- | -------------------------------------------- |
| SetRef | class | `SetRef(address, *, item_type, parent_ref=None, owner_shape=None)`   | read/write | unordered unique-element container backed by a nested set |

## Shape

`from nu.mem import ShapeRef`

| Name     | Sort  | Signature                                                       | Effect     | Meaning                                          |
| -------- | ----- | -------------------------------------------------------------------- | ---------- | --------------------------------------------------- |
| ShapeRef | class | `ShapeRef(address, *, shape_type, parent_ref=None, owner_shape=None)` | read/write | structured named-slot container backed by a nested dict; field descent yields each field's typed mem ref |

## Stdlib

`from nu.mem import BasisPointRef, ComplexRef, DateRef, DatetimeRef, DecimalRef, FractionRef, PathRef, PercentageRef, TimeRef, TimedeltaRef, TimezoneRef, UUIDRef`

Typed refs for standard-library value types. Each stores a domain value in a
different on-disk shape (`store`/`coerce` convert between them) and mixes in
the matching `nu.std` Form for its operator interface, same pattern as `IntRef`.

| Name          | Sort  | Signature                                              | Effect     | Meaning                                              |
| ------------- | ----- | --------------------------------------------------------- | ---------- | ------------------------------------------------------- |
| DecimalRef    | class | `DecimalRef(address, *, parent_ref=None, owner_shape=None)` | read/write | `Decimal` ref, stored as `str`                          |
| FractionRef   | class | `FractionRef(address, *, parent_ref=None, owner_shape=None)`| read/write | `Fraction` ref, stored as `str`                         |
| ComplexRef    | class | `ComplexRef(address, *, parent_ref=None, owner_shape=None)` | read/write | `complex` ref, stored as `str`                          |
| BasisPointRef | class | `BasisPointRef(address, *, parent_ref=None, owner_shape=None)` | read/write | basis-point ref, stored as raw `int`                    |
| PercentageRef | class | `PercentageRef(address, *, parent_ref=None, owner_shape=None)` | read/write | percentage ref, stored as raw `float`                   |
| DateRef       | class | `DateRef(address, *, parent_ref=None, owner_shape=None)`    | read/write | `date` ref, stored as ISO `str`                         |
| DatetimeRef   | class | `DatetimeRef(address, *, parent_ref=None, owner_shape=None)`| read/write | `datetime` ref, stored as ISO `str`                     |
| TimeRef       | class | `TimeRef(address, *, parent_ref=None, owner_shape=None)`    | read/write | `time` ref, stored as ISO `str`                         |
| TimedeltaRef  | class | `TimedeltaRef(address, *, parent_ref=None, owner_shape=None)` | read/write | `timedelta` ref, stored as total seconds (`float`)      |
| TimezoneRef   | class | `TimezoneRef(address, *, parent_ref=None, owner_shape=None)`| read/write | `timezone` ref, stored as offset `str`                  |
| PathRef       | class | `PathRef(address, *, parent_ref=None, owner_shape=None)`    | read/write | `Path` ref, stored as `str`                             |
| UUIDRef       | class | `UUIDRef(address, *, parent_ref=None, owner_shape=None)`    | read/write | `UUID` ref, stored as `str`                             |

## JQueue

`from nu.mem.refs.jqueue import JQueue` — optional dep `nu-mem[jqueue]`; not
yet re-exported flat at `nu.mem` (deferred pass, lands with the v2 substrate seam).

| Name   | Sort | Signature      | Effect | Meaning                                                          |
| ------ | ---- | -------------- | ------ | ------------------------------------------------------------------- |
| JQueue | Form | `JQueue(node)` | pure   | typed surface over a janus-backed queue ref; `put`/`get`/`qsize`/`close` build interaction trees over the wrapped node |

## JQueue Ref

`from nu.mem.refs.jqueue import JQueueRef`

| Name      | Sort  | Signature                                                                     | Effect     | Meaning                                                       |
| --------- | ----- | -------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------ |
| JQueueRef | class | `JQueueRef(address, *, parent_ref=None, owner_shape=None, capacity=None, item_type=object)` | read/write | leaf ref to a `janus.Queue`; vivifies it at the slot's path on first fetch, then returns the same instance |

## JQueue Interactions

`from nu.mem.refs.jqueue import Put, Get, QSize, Close, QueueClosed`

| Name        | Sort          | Signature           | Effect          | Meaning                                                       |
| ----------- | ------------- | -------------------- | --------------- | ------------------------------------------------------------------ |
| Put         | ScalarCommand | `Put(queue, value)`  | mutates slot 0  | enqueue value; blocks when full (back-pressure)                    |
| Get         | ScalarAction  | `Get(queue)`         | mutates slot 0  | pop one value; blocks when empty; mutating producer, so Action not Query |
| QSize       | ScalarQuery   | `QSize(queue)`       | pure            | snapshot item count                                                 |
| Close       | ScalarCommand | `Close(queue)`       | mutates slot 0  | shut down both queue halves                                        |

> `QueueClosed` (`Exception`) — raised by `Get` when shut down and empty, or by `Put` when shut down.

## Tree passes

`from nu.mem import inline_refs`

| Name        | Sort | Signature          | Effect | Meaning                                                             |
| ----------- | ---- | -------------------- | ------ | ----------------------------------------------------------------------|
| inline_refs | fn   | `inline_refs(tree)`  | pure   | retired no-op; runtime path resolution (parent-on-tree) superseded ref flattening |
