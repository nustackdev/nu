"""every_dict — Dict substrate for everybase.

A simple substrate where a plain nested Python dict is the data bag.
No storage backend, no views, no reactivity. Just dicts.

Alternative to every-pv when you need shapes without persistence.

Usage::

    from every_dict import Shape, ShapeRef, IntSlot, StrSlot
    from everyabc import Context

    class User(Shape):
        name = StrSlot()
        age = IntSlot()

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
from every_dict.items import ItemRef
from every_dict.ref import RefBase
from every_dict.slots import (
    BoolSlot,
    BytesSlot,
    DictSlot,
    FloatSlot,
    IntSlot,
    ItemSlot,
    ListSlot,
    ShapesDictSlot,
    ShapesListSlot,
    ShapeSlot,
    StrSlot,
)
from everyshape import ShapeBase as Shape
from everyshape import ShapeMeta, SlotDescriptor

from . import slots


__all__ = [  # noqa: RUF022
    # Modules
    "slots",
    # Shape (re-exported from everyshape)
    "Shape",
    "ShapeMeta",
    "SlotDescriptor",
    # Base ref
    "RefBase",
    # Item refs
    "ItemRef",
    # Collection refs
    "MappingRef",
    "SequenceRef",
    "ShapeRef",
    "ShapesDictRef",
    "ShapesListRef",
    # Slots
    "BoolSlot",
    "BytesSlot",
    "DictSlot",
    "FloatSlot",
    "IntSlot",
    "ItemSlot",
    "ListSlot",
    "ShapeSlot",
    "ShapesDictSlot",
    "ShapesListSlot",
    "StrSlot",
]
