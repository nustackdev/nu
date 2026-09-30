"""The refs that address a plain nested dict: one slot in a shape, one path of keys.

A slot's ref class decides what sits at its key. A leaf holds one value with
its value form mixed in. A container holds a plain list, dict or set, and the
value it declares types every descent and every read. A shape ref holds an
inner dict laid out by another Shape.

The substrate bases (``ItemRef``, ``RefBase``) are here for fabric and library
authors; a subscript never hands one back. Leaves for standard-library values
live with their library (``nustd.<lib>.mem``), and ``JQueueRef`` lives in
``nustd.queue``.
"""

from .base import RefBase
from .containers import DictRef, ListRef, SetRef, ShapeRef
from .items import BoolRef, BytesRef, FloatRef, IntRef, ItemRef, ObjectRef, StrRef
from .prog import ProgramRef


__all__ = [
    "BoolRef",
    "BytesRef",
    "DictRef",
    "FloatRef",
    "IntRef",
    "ItemRef",
    "ListRef",
    "ObjectRef",
    "ProgramRef",
    "RefBase",
    "SetRef",
    "ShapeRef",
    "StrRef",
]
