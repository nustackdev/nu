"""nu.mem: the shape fabric over plain nested Python dicts.

A Shape declares slots, each slot is a ref, and every ref is a path of keys
into one dict you hand in. No storage backend, no views, no reactivity: reads
walk the dict, writes mutate it in place, and the dict stays yours to print,
copy or dump.

A missing key on the way down reads EMPTY rather than raising, and a write
creates whatever levels it needs, so a Shape can be laid over an empty dict
and filled in as it goes.

Usage::

    import nu.mem as nm
    from nu import Context
    from nu.domains.shape import Shape

    class User(Shape):
        name = nm.StrRef.slot()
        age = nm.IntRef.slot()

    data = {}
    ctx = Context().bind(dict, data, User)

Typed leaves (``IntRef``, ``StrRef``, ``DatetimeRef``, ...) each carry their
value Form, so the ref itself is an operand. Containers (``ListRef``,
``DictRef``, ``SetRef``) hold a plain list, dict or set. ``ShapeRef``,
``ShapesListRef`` and ``ShapesDictRef`` nest Shapes inside Shapes.
``ProgramRef`` holds Nu source. ``JQueueRef``, in ``nu.mem.refs.jqueue``,
holds a live janus queue and is imported by its own path.
"""

from nu.mem import refs
from nu.mem.refs import (
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
    ProgramRef,
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
    # Refs
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
    # Submodules
    "refs",
]
