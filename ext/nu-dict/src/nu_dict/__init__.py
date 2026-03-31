"""everydict — Dict substrate for everybase.

A substrate where a plain nested Python dict is the data bag.
No storage backend, no views, no reactivity. Just dicts.

Usage::

    from nu_dict import IntRef, StrRef
    from nu import Context
    from nu.shape import Shape

    class User(Shape):
        name = StrRef.slot()
        age = IntRef.slot()

    data = {}
    ctx = Context().bind(data, dict, User)
"""

from nu_dict.meta import inline_refs
from nu_dict.refs import (
    BasisPointRef,
    BoolRef,
    BytesRef,
    ComplexRef,
    DateRef,
    DatetimeRef,
    DecimalRef,
    DictRef,
    FloatRef,
    FractionRef,
    IntRef,
    ItemRef,
    ListRef,
    PathRef,
    PercentageRef,
    RefBase,
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
    "inline_refs",
]
