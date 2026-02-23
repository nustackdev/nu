"""everydict — Dict substrate for everybase.

A substrate where a plain nested Python dict is the data bag.
No storage backend, no views, no reactivity. Just dicts.

Usage::

    from everydict import IntRef, StrRef
    from everybase import Context
    from everyshape import Shape

    class User(Shape):
        name = StrRef.slot()
        age = IntRef.slot()

    data = {}
    ctx = Context().with_handle(dict, data, scope=User)
"""

from everydict.refs import (
    BasisPointRef,
    BoolRef,
    BytesRef,
    ComplexRef,
    DateRef,
    DatetimeRef,
    DecimalRef,
    FloatRef,
    FractionRef,
    IntRef,
    ItemRef,
    MappingRef,
    PathRef,
    PercentageRef,
    RefBase,
    SequenceRef,
    SetRef,
    ShapeRef,
    ShapesDictRef,
    ShapesListRef,
    StrRef,
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
    "FloatRef",
    "FractionRef",
    "IntRef",
    "ItemRef",
    "MappingRef",
    "PathRef",
    "PercentageRef",
    "RefBase",
    "SequenceRef",
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
