"""nu_virtuals — virtuals (polymorphic views) KV-storage fabric for Nu Shapes.

Refs over virtuals views backed by a tkv snapshot / transaction.

Usage::

    from nu_virtuals import IntRef, StrRef, ShapeRef, Atomic
    from nu import Context
    from nu.domains.shape import Shape

    class User(Shape):
        name = StrRef.slot()
        age = IntRef.slot()
"""

import nu_virtuals._compat  # noqa: F401  — register virtuals view ABCs


# Register path types as invisibles value types so they serialize by value.
try:
    from invisibles.core.boxing import register_value_type
    from nu_virtuals.paths import ValuePathSer, ViewPathSer

    register_value_type(ViewPathSer, ValuePathSer)
except ImportError:
    pass

from nu_virtuals.interactions import (
    CONFLICT_ERRORS,
    Atomic,
    ClearPrimitivesUnsafeCmd,
    EnsureLayoutCmd,
    InitItemCmd,
    ItemPrimitiveDeleteUnsafeCmd,
    ItemPrimitiveGetUnsafe,
    ItemPrimitiveSetUnsafeCmd,
    ItemPrimitiveSetUnsafeParentSkipCmd,
    ItemPrimitiveStoreCmd,
    RetryOnConflict,
    ScanPrimitivesUnsafe,
    Snapshot,
    Transaction,
)
from nu_virtuals.paths import ValuePathSer, ViewPathSer
from nu_virtuals.presets import (
    memory_storage,
    rocksdb_storage,
    rocksdb_storage_inmemory,
    text_storage,
)
from nu_virtuals.refs import (
    BoolRef,
    BytesRef,
    DictRef,
    Facet,
    FloatRef,
    IntRef,
    ItemRef,
    ListRef,
    PrimitiveRef,
    SetRef,
    ShapeRef,
    ShapesDictRef,
    ShapesListRef,
    StrRef,
    ViewRef,
)
from nu_virtuals.tree import auto_atomic, inline_refs


# --- deferred during the v2 port ---------------------------------------------
# stdlib-typed refs (items_extended), write-back views (views/writeback),
# auto_flow_atomic / auto_total_atomic / optimize_primitive_reads|writes,
# PrimitiveDictRef/PrimitiveListRef/PrimitiveSetRef — re-added as each lands on
# the v2 substrate seam.


__all__ = [  # noqa: RUF022
    # Interactions — Item
    "EnsureLayoutCmd",
    "InitItemCmd",
    "ItemPrimitiveGetUnsafe",
    "ItemPrimitiveSetUnsafeCmd",
    "ItemPrimitiveSetUnsafeParentSkipCmd",
    "ItemPrimitiveDeleteUnsafeCmd",
    "ItemPrimitiveStoreCmd",
    # Interactions — Collection
    "ClearPrimitivesUnsafeCmd",
    "ScanPrimitivesUnsafe",
    # Interactions — Atomicity
    "Atomic",
    "Snapshot",
    "Transaction",
    "RetryOnConflict",
    "CONFLICT_ERRORS",
    # Tree
    "auto_atomic",
    "inline_refs",
    # Paths
    "ValuePathSer",
    "ViewPathSer",
    # Presets
    "memory_storage",
    "rocksdb_storage",
    "rocksdb_storage_inmemory",
    "text_storage",
    # Refs
    "Facet",
    "BoolRef",
    "BytesRef",
    "DictRef",
    "FloatRef",
    "IntRef",
    "ItemRef",
    "ListRef",
    "PrimitiveRef",
    "SetRef",
    "ShapeRef",
    "ShapesDictRef",
    "ShapesListRef",
    "StrRef",
    "ViewRef",
]
