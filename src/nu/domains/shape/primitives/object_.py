"""Object row: a leaf slot holding a value of no declared type, with the whole ``Object`` surface.

Each tier is the leaf capability tier plus ``Object``: the ref is an operand of
the value it names, so attribute and subscript access, ``==`` and casts build
over the read. The capability tiers come first, so ``set`` / ``erase`` /
``on_change`` act on the slot rather than descending into the value.
"""

from __future__ import annotations

from nu.forms import Object

from ..item import (
    ItemForm,
    ItemRef,
    MutableItemForm,
    MutableItemRef,
    ReactiveItemForm,
    ReactiveItemRef,
)


__all__ = [
    "MutablePyObjectForm",
    "MutablePyObjectRef",
    "PyObjectForm",
    "PyObjectRef",
    "ReactivePyObjectForm",
    "ReactivePyObjectRef",
]


class PyObjectForm(ItemForm, Object):
    """Read tier of an object slot."""


class MutablePyObjectForm(MutableItemForm, PyObjectForm):
    """Mutable tier of an object slot: adds ``set``, ``erase`` and ``init``."""


class ReactivePyObjectForm(ReactiveItemForm, MutablePyObjectForm):
    """Reactive tier of an object slot: adds ``on_change``."""


class PyObjectRef(ItemRef, PyObjectForm):
    """Object slot ref, read tier."""


class MutablePyObjectRef(MutableItemRef, MutablePyObjectForm, PyObjectRef):
    """Object slot ref, mutable tier."""


class ReactivePyObjectRef(ReactiveItemRef, ReactivePyObjectForm, MutablePyObjectRef):
    """Object slot ref, reactive tier."""
