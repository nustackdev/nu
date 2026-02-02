"""every_pv - PV refs for everybase term system.

This package provides PV (polymorphic views) based ref implementations
for the everybase term system.

Key Classes:
    Typed Refs (with operators):
        - IntRef, StrRef, FloatRef, BoolRef, BytesRef

    Generic Item Refs:
        - ItemRef, ListItemRef, DictItemRef

    Collection Refs:
        - DictRef, ListRef
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

from every_pv.collections import (
    DictRef,
    ListRef,
    ShapeRef,
    ShapesDictRef,
    ShapesListRef,
)
from every_pv.primitives import (
    BoolRef,
    BytesRef,
    DictItemRef,
    FloatRef,
    IntRef,
    ItemRef,
    ListItemRef,
    StrRef,
)
from every_pv.ref import (
    PrimitiveRef,
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
from everyshape import Shape, ShapeMeta, SlotDescriptor


__all__ = [
    # Spans
    "Atomic",
    # Typed refs (with operators)
    "BoolRef",
    "BytesRef",
    # Generic item refs
    "DictItemRef",
    # Collection refs
    "DictRef",
    "FloatRef",
    "IntRef",
    "ItemRef",
    "ListItemRef",
    "ListRef",
    # Stdtypes refs
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
    # Abstract refs
    "PrimitiveRef",
    # Shape (re-exported from everyshape)
    "Shape",
    "ShapeMeta",
    "ShapeRef",
    "ShapesDictRef",
    "ShapesListRef",
    "SlotDescriptor",
    "Snapshot",
    "StrRef",
    "ViewRef",
]
