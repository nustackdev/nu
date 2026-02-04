"""Dict substrate collections — refs for containers in nested dicts.

Base:
    RefBase         dict substrate implementation (navigate nested dicts)

Items:
    ItemRef         generic typed value holder
    IntRef, StrRef, FloatRef, BoolRef, BytesRef   typed item refs

Collections:
    ShapeRef        structured container with named slots
    MappingRef      key-value container (child ref creation)
    SequenceRef     ordered container (item ref creation)
    SetRef          unordered unique-element container
    ShapesListRef   sequence of homogeneous shapes
    ShapesDictRef   mapping of homogeneous shapes
"""

from .base import RefBase
from .dict import MappingRef
from .dictshape import ShapesDictRef
from .items import BoolRef, BytesRef, FloatRef, IntRef, ItemRef, StrRef
from .listshape import ShapesListRef
from .sequence import SequenceRef
from .set import SetRef
from .shape import ShapeRef


__all__ = [
    "BoolRef",
    "BytesRef",
    "FloatRef",
    "IntRef",
    "ItemRef",
    "MappingRef",
    "RefBase",
    "SequenceRef",
    "SetRef",
    "ShapeRef",
    "ShapesDictRef",
    "ShapesListRef",
    "StrRef",
]
