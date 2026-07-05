"""nu.mem — Nu Shapes fabric adapter for in-memory state.

Plain nested Python dicts as the data bag. No storage backend, no views,
no reactivity. Just dicts.

Usage::

    import nu.mem as nm
    from nu import Context
    from nu.domains.shape import Shape

    class User(Shape):
        name = nm.StrRef.slot()
        age = nm.IntRef.slot()

    data = {}
    ctx = Context().bind(dict, data, User)
"""

from nu.mem import refs, tree
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
from nu.mem.tree import inline_refs


# --- ported incrementally during the P2 v2 port ------------------------------
# jqueue (deferred pass) is re-added here as it lands on the v2 substrate seam.


__all__ = [
    # Submodules
    "refs",
    "tree",
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
