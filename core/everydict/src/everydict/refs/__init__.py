"""Dict substrate refs.

Base:
    RefBase         dict substrate implementation (navigate nested dicts)

Items:
    ItemRef         generic typed value holder
    IntRef, StrRef, FloatRef, BoolRef, BytesRef   typed item refs

Collections:
    ShapeRef        structured container with named slots
    DictRef         key-value container
    ListRef         ordered container
    SetRef          unordered unique-element container
    ShapesListRef   sequence of homogeneous shapes
    ShapesDictRef   mapping of homogeneous shapes
"""

from .base import RefBase
from .dict import DictRef
from .dictshape import ShapesDictRef
from .items import BoolRef, BytesRef, FloatRef, IntRef, ItemRef, StrRef
from .items_extended import (
    BasisPointRef,
    ComplexRef,
    DateRef,
    DatetimeRef,
    DecimalRef,
    FractionRef,
    PathRef,
    PercentageRef,
    TimedeltaRef,
    TimeRef,
    TimezoneRef,
    UUIDRef,
)
from .list import ListRef
from .listshape import ShapesListRef
from .set import SetRef
from .shape import ShapeRef


__all__ = [
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
    "RefBase",
    "SetRef",
    "ShapeRef",
    "ShapesDictRef",
    "ShapesListRef",
    "StrRef",
    "TimeRef",
    "TimedeltaRef",
    "TimezoneRef",
    "UUIDRef",
]
