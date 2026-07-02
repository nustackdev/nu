"""Virtuals substrate refs.

Base:
    ViewRef         refs to container views (dict, list, set, shape)
    PrimitiveRef    refs to leaf values (int, str, etc.)

Items:
    ItemRef         generic typed leaf-value holder
    IntRef, StrRef, FloatRef, BoolRef, BytesRef   typed item refs

Collections:
    ShapeRef, DictRef, ListRef, SetRef, ShapesListRef, ShapesDictRef
"""

from .base import Facet, PrimitiveRef, ViewRef
from .dict import DictRef
from .dictshape import ShapesDictRef
from .items import BoolRef, BytesRef, FloatRef, IntRef, ItemRef, StrRef
from .list import ListRef
from .listshape import ShapesListRef
from .primitives import (
    PrimitiveDictRef,
    PrimitiveFrozenSetRef,
    PrimitiveListRef,
    PrimitiveSetRef,
    PrimitiveTupleRef,
)
from .set import SetRef
from .shape import ShapeRef
from .std import (
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


__all__ = [
    "BasisPointRef",
    "BoolRef",
    "BytesRef",
    "ComplexRef",
    "DateRef",
    "DatetimeRef",
    "DecimalRef",
    "DictRef",
    "Facet",
    "FloatRef",
    "FractionRef",
    "IntRef",
    "ItemRef",
    "ListRef",
    "PathRef",
    "PercentageRef",
    "PrimitiveDictRef",
    "PrimitiveFrozenSetRef",
    "PrimitiveListRef",
    "PrimitiveRef",
    "PrimitiveSetRef",
    "PrimitiveTupleRef",
    "SetRef",
    "ShapeRef",
    "ShapesDictRef",
    "ShapesListRef",
    "StrRef",
    "TimeRef",
    "TimedeltaRef",
    "TimezoneRef",
    "UUIDRef",
    "ViewRef",
]
