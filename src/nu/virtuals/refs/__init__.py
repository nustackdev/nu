"""Virtuals substrate refs.

Base:
    ViewRef         refs to container views (dict, list, set, shape)
    PrimitiveRef    refs to leaf values (int, str, etc.)

Items:
    ItemRef         generic typed leaf-value holder
    IntRef, StrRef, FloatRef, BoolRef, BytesRef   typed item refs

Collections:
    ShapeRef, DictRef, ListRef, SetRef, ShapesListRef, ShapesDictRef
"""

from .base import Facet, PrimitiveRef, ViewRef
from .dict import DictRef
from .dictshape import ShapesDictRef
from .items import BoolRef, BytesRef, FloatRef, IntRef, ItemRef, StrRef
from .list import ListRef
from .listshape import ShapesListRef
from .set import SetRef
from .shape import ShapeRef


# --- deferred ----------------------------------------------------------------
# from .items_extended import (...)   # stdlib-typed refs -> needs nu/stdlib


__all__ = [
    "BoolRef",
    "BytesRef",
    "DictRef",
    "Facet",
    "FloatRef",
    "IntRef",
    "ItemRef",
    "ListRef",
    "PrimitiveRef",
    "SetRef",
    "ShapeRef",
    "ShapesDictRef",
    "ShapesListRef",
    "StrRef",
    "ViewRef",
]
