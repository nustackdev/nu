"""Every ref the dict substrate offers.

Base:
    RefBase         path of keys through nested dicts; all the rest build on it

Items:
    ItemRef         untyped value holder, what a container descends into
    IntRef, StrRef, FloatRef, BoolRef, BytesRef   typed leaves
    DecimalRef, FractionRef, ComplexRef, BasisPointRef, PercentageRef,
    DateRef, DatetimeRef, TimeRef, TimedeltaRef, TimezoneRef,
    PathRef, UUIDRef                              stdlib leaves, each stored
                                                  in a form a dict can hold

Collections:
    ShapeRef, DictRef, ListRef, SetRef, ShapesListRef, ShapesDictRef

Programs:
    ProgramRef      Nu source text in a slot, with the Program verbs

``JQueueRef`` lives in ``jqueue`` and is not re-exported here: it needs janus.
"""

from .base import RefBase
from .dict import DictRef
from .dictshape import ShapesDictRef
from .items import BoolRef, BytesRef, FloatRef, IntRef, ItemRef, StrRef
from .list import ListRef
from .listshape import ShapesListRef
from .prog import ProgramRef
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
    "FloatRef",
    "FractionRef",
    "IntRef",
    "ItemRef",
    "ListRef",
    "PathRef",
    "PercentageRef",
    "ProgramRef",
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
