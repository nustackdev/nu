"""eb_virtuals — virtuals adapter for everybase.

Refs over virtuals (polymorphic views) KV storage.

Usage:
    from nu_virtuals import IntRef, StrRef, ShapeRef, Atomic

    class User(Shape):
        name = StrRef.slot()
        age = IntRef.slot()
        profile = ShapeRef.slot(Profile)
"""

import nu_virtuals._compat  # noqa: F401  — register virtuals ABCs


# Register path types as invisibles value types so they serialize by value
# (pickled whole) rather than being proxied element-by-element.
try:
    from invisibles.core.boxing import register_value_type
    from nu_virtuals.paths import ValuePathSer, ViewPathSer

    register_value_type(ViewPathSer, ValuePathSer)
except ImportError:
    pass

from nu_virtuals.commands import (
    ClearPrimitivesUnsafeCmd,
    EnsureLayoutCmd,
    InitItemCmd,
    ItemPrimitiveDeleteUnsafeCmd,
    ItemPrimitiveSetUnsafeCmd,
    ItemPrimitiveSetUnsafeParentSkipCmd,
    ItemPrimitiveStoreCmd,
)
from nu_virtuals.queries import (
    ItemPrimitiveGetUnsafe,
    ScanPrimitivesUnsafe,
)
from nu_virtuals.refs import (
    BasisPointRef,
    BoolRef,
    BytesRef,
    ComplexRef,
    DateRef,
    DatetimeRef,
    DecimalRef,
    DictRef,
    FloatRef,
    FractionRef,
    IntRef,
    ItemRef,
    ListRef,
    PathRef,
    PercentageRef,
    PrimitiveDictRef,
    PrimitiveListRef,
    PrimitiveRef,
    PrimitiveSetRef,
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
from nu_virtuals.spans import Atomic, Snapshot, Transaction
from nu_virtuals.tree import (
    auto_atomic,
    inline_refs,
    optimize_primitive_reads,
    optimize_primitive_writes,
)


__all__ = [  # noqa: RUF022
    # Commands — Item
    "EnsureLayoutCmd",
    "InitItemCmd",
    "ItemPrimitiveSetUnsafeCmd",
    "ItemPrimitiveSetUnsafeParentSkipCmd",
    "ItemPrimitiveDeleteUnsafeCmd",
    "ItemPrimitiveStoreCmd",
    # Commands — Collection
    "ClearPrimitivesUnsafeCmd",
    # Queries
    "ItemPrimitiveGetUnsafe",
    "ScanPrimitivesUnsafe",
    # Tree
    "auto_atomic",
    "inline_refs",
    "optimize_primitive_reads",
    "optimize_primitive_writes",
    "Atomic",
    "BasisPointRef",
    "BoolRef",
    "BytesRef",
    "ComplexRef",
    "DateRef",
    "DatetimeRef",
    "DecimalRef",
    "DictRef",
    "FloatRef",
    "FractionRef",
    "IntRef",
    "ItemRef",
    "ListRef",
    "PathRef",
    "PercentageRef",
    "PrimitiveDictRef",
    "PrimitiveListRef",
    "PrimitiveRef",
    "PrimitiveSetRef",
    "SetRef",
    "ShapeRef",
    "ShapesDictRef",
    "ShapesListRef",
    "Snapshot",
    "Transaction",
    "StrRef",
    "TimedeltaRef",
    "TimeRef",
    "TimezoneRef",
    "UUIDRef",
    "ViewRef",
]
