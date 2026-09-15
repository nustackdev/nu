"""nustd.kv: virtuals (polymorphic views) KV-storage fabric for Nu Shapes.

Refs over virtuals views backed by a tkv snapshot / transaction.

Usage::

    from nustd.kv import IntRef, StrRef, ShapeRef, Atomic
    from nu import Context
    from nu.domains.shape import Shape

    class User(Shape):
        name = StrRef.slot()
        age = IntRef.slot()
"""

import nustd.kv._compat  # noqa: F401  (register virtuals view ABCs)
from nustd.kv import fabrics, interactions, paths, presets, refs, tree, views
from nustd.kv.interactions import (
    CONFLICT_ERRORS,
    Atomic,
    ClearPrimitivesUnsafeCmd,
    InitItemCmd,
    ItemPrimitiveDeleteUnsafeCmd,
    ItemPrimitiveGetUnsafe,
    ItemPrimitiveSetCmd,
    ItemPrimitiveSetUnsafeCmd,
    ItemPrimitiveSetUnsafeParentSkipCmd,
    Kh57Range,
    Kh57Sample,
    RetryOnConflict,
    ScanPrimitivesUnsafe,
    Snapshot,
    Transaction,
)
from nustd.kv.paths import ValuePathSer, ViewPathSer
from nustd.kv.presets import (
    inmem_observer,
    lmdb_navigator,
    lmdb_navigator_redis,
    memory_navigator,
    memory_storage,
    proxy_observer,
    redis_observer,
    rocksdb_navigator,
    rocksdb_navigator_redis,
    rocksdb_storage,
    rocksdb_storage_redis,
    served_observer,
    text_navigator,
    text_storage,
)
from nustd.kv.refs import (
    BasisPointRef,
    BoolRef,
    BytesRef,
    ComplexRef,
    DateRef,
    DatetimeRef,
    DecimalRef,
    DictRef,
    Facet,
    FloatRef,
    FractionRef,
    IntRef,
    ItemRef,
    Kh57Ref,
    Kh57ShapesRef,
    ListRef,
    PathRef,
    PercentageRef,
    PrimitiveDictRef,
    PrimitiveFrozenSetRef,
    PrimitiveListRef,
    PrimitiveRef,
    PrimitiveSetRef,
    PrimitiveTupleRef,
    ProgramRef,
    SetRef,
    ShapeRef,
    ShapesDictRef,
    ShapesListRef,
    StrRef,
    TimedeltaRef,
    TimeRef,
    TimezoneRef,
    UUIDRef,
    ViewRef,
)
from nustd.kv.tree import auto_flow_atomic


__all__ = [  # noqa: RUF022
    # Submodules
    "fabrics",
    "interactions",
    "paths",
    "presets",
    "refs",
    "tree",
    "views",
    # Interactions: Item
    "InitItemCmd",
    "ItemPrimitiveGetUnsafe",
    "ItemPrimitiveSetUnsafeCmd",
    "ItemPrimitiveSetUnsafeParentSkipCmd",
    "ItemPrimitiveDeleteUnsafeCmd",
    "ItemPrimitiveSetCmd",
    # Interactions: Collection
    "ClearPrimitivesUnsafeCmd",
    "ScanPrimitivesUnsafe",
    # Interactions: kh57
    "Kh57Sample",
    "Kh57Range",
    # Interactions: Atomicity
    "Atomic",
    "Snapshot",
    "Transaction",
    "RetryOnConflict",
    "CONFLICT_ERRORS",
    # Tree
    "auto_flow_atomic",
    # Paths
    "ValuePathSer",
    "ViewPathSer",
    # Presets - imperative (context managers)
    "memory_storage",
    "rocksdb_storage_redis",
    "rocksdb_storage",
    "text_storage",
    # Presets - bracket-form (drop into nu.With(...))
    "inmem_observer",
    "lmdb_navigator",
    "lmdb_navigator_redis",
    "memory_navigator",
    "proxy_observer",
    "redis_observer",
    "rocksdb_navigator_redis",
    "rocksdb_navigator",
    "served_observer",
    "text_navigator",
    # Refs
    "Facet",
    "BoolRef",
    "BytesRef",
    "DictRef",
    "FloatRef",
    "IntRef",
    "ItemRef",
    "Kh57Ref",
    "Kh57ShapesRef",
    "ListRef",
    "PrimitiveRef",
    "SetRef",
    "ShapeRef",
    "ShapesDictRef",
    "ShapesListRef",
    "StrRef",
    "ViewRef",
    # Refs: stdlib-typed (std)
    "BasisPointRef",
    "ComplexRef",
    "DateRef",
    "DatetimeRef",
    "DecimalRef",
    "FractionRef",
    "PathRef",
    "PercentageRef",
    "TimeRef",
    "TimedeltaRef",
    "TimezoneRef",
    "UUIDRef",
    # Refs: whole-blob compound (primitives)
    "PrimitiveDictRef",
    "PrimitiveFrozenSetRef",
    "PrimitiveListRef",
    "PrimitiveSetRef",
    "PrimitiveTupleRef",
    # Refs: stored Nu programs (prog)
    "ProgramRef",
]
