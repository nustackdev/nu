"""Object row: a leaf slot holding a value of no declared type, with the whole ``Object`` surface.

Two refs. ``ObjectRef`` is the leaf slot capability (``exists``, ``set``,
``erase``, ``init``) plus ``Object``: the ref is an operand of the value it
names, so attribute and subscript access, ``==`` and casts build over the
read. ``ReactiveObjectRef`` adds ``on_change``. The capability comes first, so
``set`` / ``erase`` / ``on_change`` act on the slot rather than descending
into the value.
"""

from __future__ import annotations

from nu.forms import Object

from ..item import MutableItemRef, ReactiveItemRef


__all__ = ["ObjectRef", "ReactiveObjectRef"]


class ObjectRef(MutableItemRef, Object):
    """Object slot ref."""


class ReactiveObjectRef(ReactiveItemRef, ObjectRef):
    """Object slot ref that can be watched: adds ``on_change``."""
