"""every_dict — Dict substrate for everybase.

A simple substrate where a plain nested Python dict is the data bag.
No storage backend, no views, no reactivity. Just dicts.

Alternative to every-pv when you need shapes without persistence.

Usage::

    from every_dict import Shape, ShapeRef, IntRef, StrRef
    from everybase import Context

    class User(Shape):
        name = StrRef.slot()
        age = IntRef.slot()

    data = {}
    ctx = Context().with_handle(dict, data, shape=User)

    root = ShapeRef(address="", shape_type=User, shape=User)
    name_val = await root.name.get().execute(ctx)
"""

from every_dict.refs import (
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
