"""every_pv - PV refs for everybase term system.

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
    from every_pv import Shape, IntRef, StrRef, ShapeRef, Atomic

    class User(Shape):
        name = StrRef.slot()
        age = IntRef.slot()
        profile = ShapeRef.slot(Profile)
"""

from every_pv.meta import auto_atomic
from every_pv.refs import (
    BoolRef,
    BytesRef,
    DictRef,
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
from every_pv.spans import Atomic, Snapshot
from every_pv.stdtypes import (
    PVBasisPointRef,
    PVComplexRef,
    PVDateRef,
    PVDatetimeRef,
    PVDecimalRef,
    PVFractionRef,
    PVPathRef,
    PVPercentageRef,
    PVTimedeltaRef,
    PVTimeRef,
    PVTimezoneRef,
    PVUUIDRef,
)


__all__ = [  # noqa: RUF022
    "auto_atomic",
    "Atomic",
    "BoolRef",
    "BytesRef",
    "DictRef",
    "FloatRef",
    "IntRef",
    "ItemRef",
    "ListRef",
    "PVBasisPointRef",
    "PVComplexRef",
    "PVDateRef",
    "PVDatetimeRef",
    "PVDecimalRef",
    "PVFractionRef",
    "PVPathRef",
    "PVPercentageRef",
    "PVTimeRef",
    "PVTimedeltaRef",
    "PVTimezoneRef",
    "PVUUIDRef",
    "SetRef",
    "PrimitiveRef",
    "ShapeRef",
    "ShapesDictRef",
    "ShapesListRef",
    "Snapshot",
    "StrRef",
    "ViewRef",
]
