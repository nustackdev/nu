"""eb_virtuals — virtuals adapter for everybase.

Refs over virtuals (polymorphic views) KV storage.

Usage:
    from nu_virtuals import IntRef, StrRef, ShapeRef, AtomicScope

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

from nu_virtuals.meta import (
    auto_atomic,
    inline_refs,
    optimize_primitive_reads,
    optimize_primitive_writes,
)
from nu_virtuals.ops import (
    AtomicScope,
    ClearPrimitivesUnsafeCmd,
    EnsureLayoutCmd,
    InitCmd,
    ItemPrimitiveDeleteUnsafeCmd,
    ItemPrimitiveGetUnsafeOp,
    ItemPrimitiveSetUnsafeCmd,
    ItemPrimitiveSetUnsafeParentSkipCmd,
    PrimitiveStoreCmd,
    ScanPrimitivesUnsafeOp,
    Snapshot,
    Transaction,
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


__all__ = [  # noqa: RUF022
    # Ops — Item
    "EnsureLayoutCmd",
    "InitCmd",
    "ItemPrimitiveGetUnsafeOp",
    "ItemPrimitiveSetUnsafeCmd",
    "ItemPrimitiveSetUnsafeParentSkipCmd",
    "ItemPrimitiveDeleteUnsafeCmd",
    # Ops — Collection
    "ScanPrimitivesUnsafeOp",
    "ClearPrimitivesUnsafeCmd",
    # Meta
    "auto_atomic",
    "inline_refs",
    "optimize_primitive_reads",
    "optimize_primitive_writes",
    "AtomicScope",
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
    "PrimitiveStoreCmd",
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
