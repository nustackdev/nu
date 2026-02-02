"""every_dict — Dict substrate for everybase.

A simple substrate where a plain nested Python dict is the data bag.
No storage backend, no views, no reactivity. Just dicts.

Alternative to every-pv when you need shapes without persistence.

Usage::

    from every_dict import Shape, ShapeRef, IntRef, StrRef
    from everyabc import Context

    class User(Shape):
        name = StrRef.slot()
        age = IntRef.slot()

    data = {}
    ctx = Context().with_handle(dict, data, shape=User)

    root = ShapeRef(address="", shape_type=User, shape=User)
    name_val = await root.name.get().execute(ctx)
"""

from every_dict.collections import (
    MappingRef,
    SequenceRef,
    ShapeRef,
    ShapesDictRef,
    ShapesListRef,
)
from every_dict.items import BoolRef, BytesRef, FloatRef, IntRef, ItemRef, StrRef
from every_dict.ref import RefBase
from every_dict.stdtypes import (
    DictBasisPointRef,
    DictComplexRef,
    DictDateRef,
    DictDatetimeRef,
    DictDecimalRef,
    DictFractionRef,
    DictPathRef,
    DictPercentageRef,
    DictTimedeltaRef,
    DictTimeRef,
    DictTimezoneRef,
    DictUUIDRef,
)
from everyshape import Shape, ShapeMeta, SlotDescriptor


__all__ = [
    # Typed item refs
    "BoolRef",
    "BytesRef",
    # Stdtypes refs
    "DictBasisPointRef",
    "DictComplexRef",
    "DictDateRef",
    "DictDatetimeRef",
    "DictDecimalRef",
    "DictFractionRef",
    "DictPathRef",
    "DictPercentageRef",
    "DictTimeRef",
    "DictTimedeltaRef",
    "DictTimezoneRef",
    "DictUUIDRef",
    "FloatRef",
    "IntRef",
    "ItemRef",
    # Collection refs
    "MappingRef",
    # Base ref
    "RefBase",
    "SequenceRef",
    # Shape (re-exported from everyshape)
    "Shape",
    "ShapeMeta",
    "ShapeRef",
    "ShapesDictRef",
    "ShapesListRef",
    "SlotDescriptor",
    "StrRef",
]
