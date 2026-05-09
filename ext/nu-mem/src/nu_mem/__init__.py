"""nu-mem — Nu Shapes fabric adapter for in-memory state.

Plain nested Python dicts as the data bag. No storage backend, no views,
no reactivity. Just dicts.

Usage::

    import nu_mem as nm
    from nu import Context
    from nu.shapes import Shape

    class User(Shape):
        name = nm.StrRef.slot()
        age = nm.IntRef.slot()

    data = {}
    ctx = Context().bind(data, dict, User)
"""

from nu_mem.refs import (
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
    JQueueForm,
    JQueueRef,
    ListRef,
    PathRef,
    PercentageRef,
    QueueClosed,
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
from nu_mem.tree import inline_refs


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
    "JQueueForm",
    "JQueueRef",
    "ListRef",
    "PathRef",
    "PercentageRef",
    "QueueClosed",
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
