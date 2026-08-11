"""nu.kv: virtuals (polymorphic views) KV-storage fabric for Nu Shapes.

Refs over virtuals views backed by a tkv snapshot / transaction.

Usage::

    from nu.kv import IntRef, StrRef, ShapeRef, Atomic
    from nu import Context
    from nu.domains.shape import Shape

    class User(Shape):
        name = StrRef.slot()
        age = IntRef.slot()
"""

import nu.kv._compat  # noqa: F401  (register virtuals view ABCs)


# Register path types as invisibles value types so they serialize by value.
try:
    from invisibles.core.boxing import register_value_type
    from nu.kv.paths import ValuePathSer, ViewPathSer

    register_value_type(ViewPathSer, ValuePathSer)
except ImportError:
    pass

from nu.kv import fabrics, interactions, paths, presets, refs, tree, views
from nu.kv.interactions import (
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
from nu.kv.paths import ValuePathSer, ViewPathSer
from nu.kv.presets import (
    inmem_observer,
    lmdb_navigator,
    lmdb_navigator_redis,
    memory_navigator,
    memory_storage,
    redis_observer,
    rocksdb_navigator,
    rocksdb_navigator_redis,
    rocksdb_storage,
    rocksdb_storage_redis,
    text_navigator,
    text_storage,
)
from nu.kv.refs import (
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
from nu.kv.tree import auto_flow_atomic, inline_refs


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
    "inline_refs",
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
    "redis_observer",
    "rocksdb_navigator_redis",
    "rocksdb_navigator",
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
]
