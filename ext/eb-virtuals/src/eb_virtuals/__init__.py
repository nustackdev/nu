"""eb_virtuals — virtuals adapter for everybase.

Refs over virtuals (polymorphic views) KV storage.

Usage:
    from eb_virtuals import IntRef, StrRef, ShapeRef, Atomic

    class User(Shape):
        name = StrRef.slot()
        age = IntRef.slot()
        profile = ShapeRef.slot(Profile)
"""

from eb_virtuals.meta import (
    auto_atomic,
    inline_refs,
    optimize_primitive_reads,
    optimize_primitive_writes,
)
from eb_virtuals.morphisms import (
    ClearPrimitivesUnsafeCmd,
    InitCmd,
    ItemPrimitiveDeleteUnsafeCmd,
    ItemPrimitiveGetUnsafeOp,
    ItemPrimitiveSetUnsafeCmd,
    ItemPrimitiveSetUnsafeParentSkipCmd,
    ScanPrimitivesUnsafeOp,
)
from eb_virtuals.refs import (
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
    PrimitiveRef,
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
from eb_virtuals.spans import Atomic, Snapshot, Transaction


__all__ = [  # noqa: RUF022
    # Morphisms — Item
    "InitCmd",
    "ItemPrimitiveGetUnsafeOp",
    "ItemPrimitiveSetUnsafeCmd",
    "ItemPrimitiveSetUnsafeParentSkipCmd",
    "ItemPrimitiveDeleteUnsafeCmd",
    # Morphisms — Collection
    "ScanPrimitivesUnsafeOp",
    "ClearPrimitivesUnsafeCmd",
    # Meta
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
    "PrimitiveRef",
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
