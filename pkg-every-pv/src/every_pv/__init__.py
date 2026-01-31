"""every_pv - PV refs for everybase term system.

This package provides PV (polymorphic views) based ref implementations
for the everybase term system.

Key Classes:
    Concrete PV Refs:
        - IntRef, StrRef, FloatRef, BoolRef, BytesRef
        - ItemRef, ListItemRef, DictItemRef
        - DictRef, ListRef
        - ShapeRef, ShapesListRef, ShapesDictRef

    Slots:
        - IntSlot, StrSlot, FloatSlot, BoolSlot, BytesSlot
        - ItemSlot, DictSlot, ListSlot
        - ShapeSlot, ShapesListSlot, ShapesDictSlot

    Spans:
        - Atomic: Transaction/snapshot boundary (auto-selects based on purity)
        - Snapshot: Read-only snapshot boundary

Usage:
    from every_pv import IntRef, StrRef, IntSlot, Atomic
"""

from every_pv.collections import (
    DictRef,
    ListRef,
    ShapeRef,
    ShapesDictRef,
    ShapesListRef,
)
from every_pv.morphisms import TypedSetCmd
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
from every_pv.spans import Atomic, Snapshot
from everyshape import ShapeBase as Shape
from everyshape import ShapeMeta, SlotDescriptor

from . import slots


__all__ = [  # noqa: RUF022
    # Modules
    "slots",
    # Shape (re-exported from everyshape)
    "Shape",
    "ShapeMeta",
    "SlotDescriptor",
    # Spans
    "Atomic",
    "Snapshot",
    # Morphisms
    "TypedSetCmd",
    # Concrete refs - Primitives
    "BoolRef",
    "BytesRef",
    "DictItemRef",
    "FloatRef",
    "IntRef",
    "ItemRef",
    "ListItemRef",
    "StrRef",
    # Concrete refs - Collections
    "DictRef",
    "ListRef",
    "ShapeRef",
    "ShapesDictRef",
    "ShapesListRef",
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
    "PrimitiveRef",
    "ViewRef",
]
