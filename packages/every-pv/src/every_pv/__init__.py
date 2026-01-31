"""every_pv - PV refs for everybase term system.

This package provides PV (polymorphic views) based ref implementations
for the everybase term system.

Key Classes:
    Concrete PV Refs:
        - PVIntRef, PVStrRef, PVFloatRef, PVBoolRef, PVBytesRef
        - PVItemRef, PVListItemRef, PVDictItemRef
        - PVDictRef, PVListRef
        - PVShapeRef, PVShapesListRef, PVShapesDictRef

    Slots:
        - IntSlot, StrSlot, FloatSlot, BoolSlot, BytesSlot
        - ItemSlot, DictSlot, ListSlot
        - ShapeSlot, ShapesListSlot, ShapesDictSlot

    Spans:
        - PVAtomic: Transaction/snapshot boundary (auto-selects based on purity)
        - PVSnapshot: Read-only snapshot boundary

Usage:
    from every_pv import PVIntRef, PVStrRef, IntSlot, PVAtomic
"""

from every_pv.collections import (
    PVDictRef,
    PVListRef,
    PVShapeRef,
    PVShapesDictRef,
    PVShapesListRef,
)
from every_pv.morphisms import TypedSetCmd
from every_pv.primitives import (
    PVBoolRef,
    PVBytesRef,
    PVDictItemRef,
    PVFloatRef,
    PVIntRef,
    PVItemRef,
    PVListItemRef,
    PVStrRef,
)
from every_pv.ref import (
    PVPrimitiveRef,
    PVViewRef,
)
from every_pv.slots import (
    BoolSlot,
    BytesSlot,
    DictSlot,
    FloatSlot,
    IntSlot,
    ItemSlot,
    ListSlot,
    ShapesDictSlot,
    ShapesListSlot,
    ShapeSlot,
    StrSlot,
)
from every_pv.spans import PVAtomic, PVSnapshot
from everyshape import ShapeBase as PVShape
from everyshape import ShapeMeta as PVShapeMeta
from everyshape import SlotDescriptor

from . import slots


__all__ = [  # noqa: RUF022
    # Modules
    "slots",
    # Shape (re-exported from everyshape)
    "PVShape",
    "PVShapeMeta",
    "SlotDescriptor",
    # Spans
    "PVAtomic",
    "PVSnapshot",
    # Morphisms
    "TypedSetCmd",
    # Concrete PV refs - Primitives
    "PVBoolRef",
    "PVBytesRef",
    "PVDictItemRef",
    "PVFloatRef",
    "PVIntRef",
    "PVItemRef",
    "PVListItemRef",
    "PVStrRef",
    # Concrete PV refs - Collections
    "PVDictRef",
    "PVListRef",
    "PVShapeRef",
    "PVShapesDictRef",
    "PVShapesListRef",
    # Slots
    "BoolSlot",
    "BytesSlot",
    "DictSlot",
    "FloatSlot",
    "IntSlot",
    "ItemSlot",
    "ListSlot",
    "ShapeSlot",
    "ShapesDictSlot",
    "ShapesListSlot",
    "StrSlot",
    # Abstract refs
    "PVPrimitiveRef",
    "PVViewRef",
]
