---
title: nu.virtuals
---

KV-storage fabric adapter: virtual collections layered over any tkv backend (in-memory, LMDB, RocksDB, text). Views decompose containers into per-element storage; refs navigate the view hierarchy against a snapshot or transaction resolved from the Context. Persistent, paged, composable through view types. Aliased as `nu.v`.

## Base

`from nu.v import ViewRef, PrimitiveRef, Facet`

| Name         | Sort  | Signature                                                                     | Effect     | Meaning                                                                    |
| ------------ | ----- | ------------------------------------------------------------------------------ | ---------- | -------------------------------------------------------------------------- |
| ViewRef      | class | `ViewRef(address, *, view_type=None, parent_ref=None, owner_shape=None)`      | read/write | ref to a container view; navigates and returns a live faceted virtuals View |
| PrimitiveRef | class | `PrimitiveRef(address, *, value_type, parent_ref=None, owner_shape=None)`     | read/write | ref to a leaf value; navigates to the parent view and subscripts the address |
| Facet        | Enum  | `Facet.NONE / LAZY / EAGER`                                                    | pure       | view facet applied on fetch; `.lazy` / `.eager` properties on ViewRef switch it |

## Items

`from nu.v import ItemRef, IntRef, StrRef, FloatRef, BoolRef, BytesRef`

| Name     | Sort  | Signature                                                                                          | Effect     | Meaning                                                                          |
| -------- | ----- | --------------------------------------------------------------------------------------------------- | ---------- | -------------------------------------------------------------------------------- |
| ItemRef  | class | `ItemRef(address, *, value_type, value_value_type, parent_ref=None, owner_shape=None)`             | read/write | generic typed leaf-value holder on the virtuals substrate                        |
| IntRef   | class | `IntRef(address, *, parent_ref=None, owner_shape=None)`                                             | read/write | virtuals integer ref with full numeric interface (`Int` mixin); adds `inc`/`dec` |
| StrRef   | class | `StrRef(address, *, parent_ref=None, owner_shape=None)`                                             | read/write | virtuals string ref with full string interface (`Str` mixin)                     |
| FloatRef | class | `FloatRef(address, *, parent_ref=None, owner_shape=None)`                                           | read/write | virtuals float ref with full numeric interface (`Float` mixin)                   |
| BoolRef  | class | `BoolRef(address, *, parent_ref=None, owner_shape=None)`                                            | read/write | virtuals boolean ref with full logical interface (`Bool` mixin)                  |
| BytesRef | class | `BytesRef(address, *, parent_ref=None, owner_shape=None)`                                           | read/write | virtuals bytes ref with full bytes interface (`Bytes` mixin)                     |

## Dict

`from nu.v import DictRef`

| Name    | Sort  | Signature                                                                                                              | Effect     | Meaning                                                             |
| ------- | ----- | ----------------------------------------------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------- |
| DictRef | class | `DictRef(address, *, value_type, key_type, key_value_type, value_value_type, view_type, parent_ref=None, owner_shape=None)` | read/write | key-value mapping backed by a virtuals mapping view (default `DictView`) |

## Dict Shapes

`from nu.v import ShapesDictRef`

| Name          | Sort  | Signature                                                                                                             | Effect     | Meaning                                                                       |
| ------------- | ----- | ---------------------------------------------------------------------------------------------------------------------- | ---------- | ----------------------------------------------------------------------------- |
| ShapesDictRef | class | `ShapesDictRef(address, *, shape_type, key_type, key_value_type, view_type=None, parent_ref=None, owner_shape=None)` | read/write | mapping of homogeneous shapes; key descent yields a substrate-backed `ShapeRef` |

## List

`from nu.v import ListRef`

| Name    | Sort  | Signature                                                                                        | Effect     | Meaning                                                          |
| ------- | ----- | ------------------------------------------------------------------------------------------------- | ---------- | ---------------------------------------------------------------- |
| ListRef | class | `ListRef(address, *, item_type, item_value_type, view_type, parent_ref=None, owner_shape=None)` | read/write | ordered element container backed by a virtuals sequence view (default `ListView`) |

## List Shapes

`from nu.v import ShapesListRef`

| Name          | Sort  | Signature                                                                                     | Effect     | Meaning                                                                            |
| ------------- | ----- | ---------------------------------------------------------------------------------------------- | ---------- | ---------------------------------------------------------------------------------- |
| ShapesListRef | class | `ShapesListRef(address, *, shape_type, view_type=None, parent_ref=None, owner_shape=None)`   | read/write | sequence of homogeneous shapes; index descent yields a substrate-backed `ShapeRef` |

## Set

`from nu.v import SetRef`

| Name   | Sort  | Signature                                                                          | Effect     | Meaning                                                                |
| ------ | ----- | ----------------------------------------------------------------------------------- | ---------- | ---------------------------------------------------------------------- |
| SetRef | class | `SetRef(address, *, item_type, view_type, parent_ref=None, owner_shape=None)`     | read/write | unordered unique-element container backed by a virtuals set view (default `SetView`) |

## Shape

`from nu.v import ShapeRef`

| Name     | Sort  | Signature                                                                                       | Effect     | Meaning                                                                                          |
| -------- | ----- | ------------------------------------------------------------------------------------------------ | ---------- | ------------------------------------------------------------------------------------------------ |
| ShapeRef | class | `ShapeRef(address, *, shape_type, view_type=None, parent_ref=None, owner_shape=None)`          | read/write | structured named-slot container backed by a mapping view; field descent yields each field's typed virtuals ref |

## Kh57

`from nu.v import Kh57Ref, Kh57ShapesRef`

Sparse int-keyed maps laid out under kh57-encoded child segments so range reservoir sampling runs with low read amplification. Keys are non-negative 57-bit ints; default view is `Kh57View`. Both add `.sample(n, begin, end)` and `.range(begin, end)` on top of the standard mapping surface.

| Name          | Sort  | Signature                                                                                             | Effect     | Meaning                                                                        |
| ------------- | ----- | ------------------------------------------------------------------------------------------------------ | ---------- | ------------------------------------------------------------------------------ |
| Kh57Ref       | class | `Kh57Ref(address, *, value_type, value_value_type, view_type=None, parent_ref=None, owner_shape=None)` | read/write | sparse int-keyed mapping of primitive values with kh57 sampling                |
| Kh57ShapesRef | class | `Kh57ShapesRef(address, *, shape_type, view_type=None, parent_ref=None, owner_shape=None)`           | read/write | sparse int-keyed mapping of homogeneous shapes with kh57 sampling; key descent yields a `ShapeRef` |

## Stdlib

`from nu.v import BasisPointRef, ComplexRef, DateRef, DatetimeRef, DecimalRef, FractionRef, PathRef, PercentageRef, TimeRef, TimedeltaRef, TimezoneRef, UUIDRef`

Typed leaf refs for standard-library value types. Each overrides `_lift` / `set` to convert between the domain value and its on-disk form, and mixes in the matching `nu.std` Form for its operator interface, same pattern as `IntRef`.

| Name          | Sort  | Signature                                                     | Effect     | Meaning                                              |
| ------------- | ----- | ------------------------------------------------------------- | ---------- | ---------------------------------------------------- |
| DecimalRef    | class | `DecimalRef(address, *, parent_ref=None, owner_shape=None)`  | read/write | `Decimal` ref, stored as `str`                       |
| FractionRef   | class | `FractionRef(address, *, parent_ref=None, owner_shape=None)` | read/write | `Fraction` ref, stored as `str`                      |
| ComplexRef    | class | `ComplexRef(address, *, parent_ref=None, owner_shape=None)`  | read/write | `complex` ref, stored as `str`                       |
| BasisPointRef | class | `BasisPointRef(address, *, parent_ref=None, owner_shape=None)` | read/write | basis-point ref, stored as raw `int`                 |
| PercentageRef | class | `PercentageRef(address, *, parent_ref=None, owner_shape=None)` | read/write | percentage ref, stored as raw `float`                |
| DateRef       | class | `DateRef(address, *, parent_ref=None, owner_shape=None)`     | read/write | `date` ref, stored as ISO `str`                      |
| DatetimeRef   | class | `DatetimeRef(address, *, parent_ref=None, owner_shape=None)` | read/write | `datetime` ref, stored as ISO `str`                  |
| TimeRef       | class | `TimeRef(address, *, parent_ref=None, owner_shape=None)`     | read/write | `time` ref, stored as ISO `str`                      |
| TimedeltaRef  | class | `TimedeltaRef(address, *, parent_ref=None, owner_shape=None)` | read/write | `timedelta` ref, stored as total seconds (`float`)   |
| TimezoneRef   | class | `TimezoneRef(address, *, parent_ref=None, owner_shape=None)` | read/write | `timezone` ref, stored as offset `str`               |
| PathRef       | class | `PathRef(address, *, parent_ref=None, owner_shape=None)`     | read/write | `Path` ref, stored as `str`                          |
| UUIDRef       | class | `UUIDRef(address, *, parent_ref=None, owner_shape=None)`     | read/write | `UUID` ref, stored as `str`                          |

## Primitive blobs

`from nu.v import PrimitiveDictRef, PrimitiveListRef, PrimitiveSetRef, PrimitiveFrozenSetRef, PrimitiveTupleRef`

Whole-blob compound refs: the container is written as one opaque value via `ItemPrimitiveSetCmd` and read back as a plain Python object. Use for heterogeneous or opaque containers that should round-trip whole rather than shape-decompose. Each mixes in the matching collection Form so the value still carries its full interface.

| Name                  | Sort  | Signature                                                             | Effect     | Meaning                                       |
| --------------------- | ----- | --------------------------------------------------------------------- | ---------- | --------------------------------------------- |
| PrimitiveListRef      | class | `PrimitiveListRef(address, *, parent_ref=None, owner_shape=None)`    | read/write | `list` stored as a single primitive blob      |
| PrimitiveDictRef      | class | `PrimitiveDictRef(address, *, parent_ref=None, owner_shape=None)`    | read/write | `dict` stored as a single primitive blob      |
| PrimitiveTupleRef     | class | `PrimitiveTupleRef(address, *, parent_ref=None, owner_shape=None)`   | read/write | `tuple` stored as a single primitive blob     |
| PrimitiveSetRef       | class | `PrimitiveSetRef(address, *, parent_ref=None, owner_shape=None)`     | read/write | `set` stored as a single primitive blob       |
| PrimitiveFrozenSetRef | class | `PrimitiveFrozenSetRef(address, *, parent_ref=None, owner_shape=None)` | read/write | `frozenset` stored as a single primitive blob |

## Atomicity

`from nu.v import Atomic, Snapshot, Transaction, RetryOnConflict, CONFLICT_ERRORS`

Bracket the body to open a read-only snapshot or a write transaction on the resolved Navigator, scoped into the ctx for the body's duration. Snapshots close on exit; transactions commit on clean exit, abort on error.

| Name            | Sort   | Signature                                                                          | Effect         | Meaning                                                                                       |
| --------------- | ------ | ----------------------------------------------------------------------------------- | -------------- | --------------------------------------------------------------------------------------------- |
| Atomic          | fn     | `Atomic(*children, scope=None)`                                                    | pure           | picks `Transaction` if the body has any tracked write, else `Snapshot`                        |
| Snapshot        | Form   | `Snapshot(*children, scope=None)`                                                  | READ           | read-only snapshot boundary; scopes `SnapshotProtocol` under `scope` into ctx                 |
| Transaction     | Form   | `Transaction(*children, scope=None)`                                               | WRITE          | write transaction boundary; scopes `TransactionProtocol` under `scope` into ctx               |
| RetryOnConflict | Form   | `RetryOnConflict(body, *, max_attempts=5, delay=0.1, backoff=2.0, jitter=0.5, ...)` | RESOLVE        | `Retry` preset for `StorageTransactionConflictError` and `StorageLockTimeoutError` only       |
| CONFLICT_ERRORS | tuple  | `(StorageTransactionConflictError, StorageLockTimeoutError)`                       | pure           | the two error types `RetryOnConflict` retries on by default                                   |

## Item interactions

`from nu.v import InitItemCmd, ItemPrimitiveGetUnsafe, ItemPrimitiveSetCmd, ItemPrimitiveSetUnsafeCmd, ItemPrimitiveSetUnsafeParentSkipCmd, ItemPrimitiveDeleteUnsafeCmd`

Optimization internals for tree deformers, not user-facing APIs. The `Unsafe` variants require virtuals views with `UnsafePrimitiveOpsBase` in MRO. The leaf ref rides at `children[0]`.

| Name                                | Sort          | Signature                                        | Effect | Meaning                                                                            |
| ----------------------------------- | ------------- | ------------------------------------------------- | ------ | ---------------------------------------------------------------------------------- |
| InitItemCmd                         | ScalarCommand | `InitItemCmd(ref)`                                | WRITE  | materialize the container chain by fetching the view                               |
| ItemPrimitiveGetUnsafe              | ScalarQuery   | `ItemPrimitiveGetUnsafe(ref)`                    | READ   | leaf read via `_unsafe_primitive_read` (single ctx.get)                            |
| ItemPrimitiveSetCmd                 | ScalarCommand | `ItemPrimitiveSetCmd(ref, value)`                | WRITE  | store a value via `_primitive_write`, bypassing container type checks              |
| ItemPrimitiveSetUnsafeCmd           | ScalarCommand | `ItemPrimitiveSetUnsafeCmd(ref, value)`          | WRITE  | leaf write via `_unsafe_primitive_write(ensure_exists=True)`                       |
| ItemPrimitiveSetUnsafeParentSkipCmd | ScalarCommand | `ItemPrimitiveSetUnsafeParentSkipCmd(ref, value)` | WRITE  | leaf write via `_unsafe_primitive_write()` (full parent skip)                      |
| ItemPrimitiveDeleteUnsafeCmd        | ScalarCommand | `ItemPrimitiveDeleteUnsafeCmd(ref)`              | WRITE  | leaf delete via `_unsafe_primitive_delete`                                         |

## Collection interactions

`from nu.v import ScanPrimitivesUnsafe, ClearPrimitivesUnsafeCmd`

Optimization internals for container views with `UnsafePrimitiveOpsBase` in MRO. The container view ref rides at `children[0]`.

| Name                     | Sort          | Signature                        | Effect | Meaning                                                             |
| ------------------------ | ------------- | --------------------------------- | ------ | ------------------------------------------------------------------- |
| ScanPrimitivesUnsafe     | ScalarQuery   | `ScanPrimitivesUnsafe(ref)`      | READ   | scan all direct primitive child values via `_unsafe_primitive_scan_values` |
| ClearPrimitivesUnsafeCmd | ScalarCommand | `ClearPrimitivesUnsafeCmd(ref)`  | WRITE  | clear all primitive children via `_unsafe_primitive_clear`          |

## Kh57 interactions

`from nu.v import Kh57Sample, Kh57Range`

Range reservoir sampling atoms over a `Kh57View`. Both are deterministic given the view's salt and a seeded rng. The container view ref rides at `children[0]`; parameters live at slots 1..3.

| Name       | Sort        | Signature                                    | Effect | Meaning                                                                                   |
| ---------- | ----------- | --------------------------------------------- | ------ | ----------------------------------------------------------------------------------------- |
| Kh57Sample | ScalarQuery | `Kh57Sample(ref, n, begin=None, end=None, *, rng=None)` | READ   | up to `n` `(int_key, value)` samples from `[begin, end)`, stable under out-of-range appends |
| Kh57Range  | ScalarQuery | `Kh57Range(ref, begin, end)`                 | READ   | list of `(int_key, value)` pairs in `[begin, end)`, ascending int-key order               |

## Storage presets (imperative)

`from nu.v import memory_storage, rocksdb_storage, rocksdb_storage_redis, text_storage`

Context managers that yield a ready `StorageProtocol` for hand-wired Contexts. Persistence and codec picked per preset; each pairs a matching publisher.

| Name                  | Sort | Signature                                                                                        | Effect | Meaning                                                              |
| --------------------- | ---- | ------------------------------------------------------------------------------------------------- | ------ | -------------------------------------------------------------------- |
| memory_storage        | fn   | `memory_storage()`                                                                               | pure   | in-memory storage, no-op codec, in-memory publisher; ephemeral       |
| text_storage          | fn   | `text_storage(path)`                                                                             | pure   | JSON text storage at `path`, text codec, in-memory publisher         |
| rocksdb_storage       | fn   | `rocksdb_storage(path, read_only=False, secondary_path=None, secondary_refresh_interval=0.01)`   | pure   | RocksDB at `path`, binary codec, in-memory publisher                 |
| rocksdb_storage_redis | fn   | `rocksdb_storage_redis(path, ..., redis_url="redis://localhost:6379", channel_prefix="__every__")` | pure   | RocksDB at `path`, binary codec, Redis publisher for cross-process notifications |

## Navigator presets (bracket-form)

`from nu.v import memory_navigator, lmdb_navigator, lmdb_navigator_redis, rocksdb_navigator, rocksdb_navigator_redis, text_navigator, inmem_observer, redis_observer`

Each factory returns a single `With(...)` bracket that peers `Provide`s the whole Codec + Transport + Publisher + Observer + Storage + Navigator stack. `tags=` folds onto Storage and Navigator bindings so a shard can pick its storage.

| Name                    | Sort | Signature                                                                                                  | Effect | Meaning                                                                        |
| ----------------------- | ---- | ----------------------------------------------------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------ |
| memory_navigator        | fn   | `memory_navigator(*, tags=())`                                                                             | pure   | in-mem full stack: NoOpCodec + InMemory Transport/Publisher/Observer/Storage + Navigator |
| text_navigator          | fn   | `text_navigator(path, *, tags=(), read_only=False, log_operations=False)`                                  | pure   | text (JSON) storage full stack; in-mem transport/publisher/observer            |
| lmdb_navigator          | fn   | `lmdb_navigator(path, *, tags=(), read_only=False, map_size=10GiB, max_readers=126, subdir=True, sync=True)` | pure   | LMDB full stack; in-mem transport/publisher/observer                           |
| lmdb_navigator_redis    | fn   | `lmdb_navigator_redis(path, *, tags=(), ..., redis_url="redis://localhost:6379", channel_prefix="nu")`     | pure   | LMDB storage + Redis publisher/observer for cross-process notifications        |
| rocksdb_navigator       | fn   | `rocksdb_navigator(path, *, tags=(), read_only=False, secondary_path=None, secondary_refresh_interval=0.01, disable_wal=False, options=None)` | pure   | RocksDB full stack; in-mem transport/publisher/observer                        |
| rocksdb_navigator_redis | fn   | `rocksdb_navigator_redis(path, *, tags=(), ..., redis_url="redis://localhost:6379", channel_prefix="__every__")` | pure   | RocksDB + Redis publisher/observer for cross-process notifications             |
| inmem_observer          | fn   | `inmem_observer()`                                                                                         | pure   | Transport + Observer only; consume same-process notifications without owning storage |
| redis_observer          | fn   | `redis_observer(redis_url="redis://localhost:6379", channel_prefix="nu")`                                  | pure   | Redis Observer only; cross-process read-only subscriber                        |

## Paths

`from nu.v import ViewPathSer, ValuePathSer`

Tuple subclasses used as serializable navigation paths, registered as invisibles value types so paths pickle by value rather than proxy element-by-element.

| Name         | Sort  | Signature                        | Effect | Meaning                                                                     |
| ------------ | ----- | -------------------------------- | ------ | --------------------------------------------------------------------------- |
| ViewPathSer  | class | `ViewPathSer((addr, view_type), ...)` | pure   | serializable path to a view; sequence of `(address, view_type)` segments    |
| ValuePathSer | class | `ValuePathSer((addr, marker), ..., (addr, value_type))` | pure   | serializable path to a value; view segments plus a final `(address, value_type)` |

## Tree passes

`from nu.v import auto_flow_atomic, inline_refs`

| Name             | Sort | Signature                       | Effect | Meaning                                                                                          |
| ---------------- | ---- | -------------------------------- | ------ | ------------------------------------------------------------------------------------------------ |
| auto_flow_atomic | fn   | `auto_flow_atomic(tree, scope=None)` | pure   | bottom-up wrap non-Flow children of every Flow: `Transaction` if any write in scope, else `Snapshot` |
| inline_refs      | fn   | `inline_refs(tree)`             | pure   | retired no-op; runtime path resolution superseded ref flattening                                 |
