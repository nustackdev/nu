"""The refs that address a plain nested dict: one slot in a shape, one path of keys.

A slot's ref class decides what sits at its key. A leaf holds one value with
its value form mixed in. A container holds a plain list, dict or set, and the
value it declares types every descent and every read. A shape ref holds an
inner dict laid out by another Shape.

The substrate bases (``ItemRef``, ``RefBase``) are here for fabric and library
authors; a subscript never hands one back. ``JQueueRef`` lives in ``jqueue``
and is not re-exported here: it needs janus.
"""

from .base import RefBase
from .containers import DictRef, ListRef, SetRef, ShapeRef
from .items import BoolRef, BytesRef, FloatRef, IntRef, ItemRef, ObjectRef, StrRef
from .prog import ProgramRef
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
    "ObjectRef",
    "PathRef",
    "PercentageRef",
    "ProgramRef",
    "RefBase",
    "SetRef",
    "ShapeRef",
    "StrRef",
    "TimeRef",
    "TimedeltaRef",
    "TimezoneRef",
    "UUIDRef",
]
