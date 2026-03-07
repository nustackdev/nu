"""eb_pv - PV adapter for everybase.

This package provides PV (polymorphic views) based ref implementations
for the everybase term system.

Key Classes:
    Typed Refs (with operators):
        - IntRef, StrRef, FloatRef, BoolRef, BytesRef

    Generic Item Ref:
        - ItemRef

    Collection Refs:
        - DictRef, ListRef, SetRef
        - ShapeRef, ShapesListRef, ShapesDictRef

    Spans:
        - Atomic: Transaction/snapshot boundary (auto-selects based on purity)
        - Snapshot: Read-only snapshot boundary

Usage:
    from eb_pv import Shape, IntRef, StrRef, ShapeRef, Atomic

    class User(Shape):
        name = StrRef.slot()
        age = IntRef.slot()
        profile = ShapeRef.slot(Profile)
"""

from eb_pv.meta import (
    auto_atomic,
    inline_refs,
    optimize_primitive_reads,
    optimize_primitive_writes,
)
from eb_pv.morphisms import (
    ClearPrimitivesUnsafeCmd,
    InitCmd,
    ItemPrimitiveDeleteUnsafeCmd,
    ItemPrimitiveGetUnsafeOp,
    ItemPrimitiveSetUnsafeCmd,
    ItemPrimitiveSetUnsafeParentSkipCmd,
    ScanPrimitivesUnsafeOp,
)
from eb_pv.refs import (
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
from eb_pv.spans import Atomic, Snapshot, Transaction


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
