"""PV substrate collections — refs for containers in PV view hierarchy.

Base:
    RefBase         PV substrate base (path resolution, view navigation)
    PrimitiveRef    refs to leaf values (int, str, etc.)
    ViewRef         refs to container views (dict, list, set)

Items:
    ItemRef, ListItemRef, DictItemRef   document-model item refs
    IntRef, StrRef, FloatRef, BoolRef, BytesRef   typed primitive refs

Collections:
    ShapeRef        structured container with named slots
    DictRef         key-value container (child ref creation)
    ListRef         ordered container (item ref creation)
    ShapesListRef   sequence of homogeneous shapes
    ShapesDictRef   mapping of homogeneous shapes
"""

from .base import PrimitiveRef, RefBase, ViewRef
from .dict import DictRef
from .dictshape import ShapesDictRef
from .items import (
    BoolRef,
    BytesRef,
    DictItemRef,
    FloatRef,
    IntRef,
    ItemRef,
    ListItemRef,
    StrRef,
)
from .list import ListRef
from .listshape import ShapesListRef
from .shape import ShapeRef


__all__ = [
    "BoolRef",
    "BytesRef",
    "DictItemRef",
    "DictRef",
    "FloatRef",
    "IntRef",
    "ItemRef",
    "ListItemRef",
    "ListRef",
    "PrimitiveRef",
    "RefBase",
    "SequenceRef",
    "ShapeRef",
    "ShapesDictRef",
    "ShapesListRef",
    "StrRef",
    "ViewRef",
]
