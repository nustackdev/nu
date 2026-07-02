"""Dict substrate refs.

Base:
    RefBase         dict substrate implementation (navigate nested dicts)

Items:
    ItemRef         generic typed value holder
    IntRef, StrRef, FloatRef, BoolRef, BytesRef   typed item refs

Collections (ported incrementally during the P2 v2 port):
    ShapeRef, DictRef, ListRef, SetRef, ShapesListRef, ShapesDictRef
"""

from .base import RefBase
from .dict import DictRef
from .dictshape import ShapesDictRef
from .items import BoolRef, BytesRef, FloatRef, IntRef, ItemRef, StrRef
from .list import ListRef
from .listshape import ShapesListRef
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


# --- deferred ----------------------------------------------------------------
# from .jqueue import JQueueForm, JQueueRef, QueueClosed   # deferred pass


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
