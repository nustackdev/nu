"""PV substrate collections — refs for containers in PV view hierarchy.

Base:
    PrimitiveRef    refs to leaf values (int, str, etc.)
    ViewRef         refs to container views (dict, list, set)

Items:
    ItemRef                                        document-model item ref
    IntRef, StrRef, FloatRef, BoolRef, BytesRef    typed primitive refs
    PrimitiveDictRef, PrimitiveListRef, PrimitiveSetRef    compound primitive refs (blob storage)

Collections:
    ShapeRef        structured container with named slots
    DictRef         key-value container (child ref creation)
    ListRef         ordered container (item ref creation)
    SetRef          unordered unique-element container
    ShapesListRef   sequence of homogeneous shapes
    ShapesDictRef   mapping of homogeneous shapes
"""

from .base import PrimitiveRef, ViewRef
from .dict import DictRef
from .dictshape import ShapesDictRef
from .items import (
    BoolRef,
    BytesRef,
    FloatRef,
    IntRef,
    ItemRef,
    PrimitiveDictRef,
    PrimitiveListRef,
    PrimitiveSetRef,
    StrRef,
)
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
    "PrimitiveDictRef",
    "PrimitiveListRef",
    "PrimitiveRef",
    "PrimitiveSetRef",
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
