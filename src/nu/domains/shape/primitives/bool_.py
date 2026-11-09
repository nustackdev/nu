"""Bool row: a leaf slot holding a ``bool``, with the whole ``Bool`` surface.

Each tier is the leaf capability tier plus ``Bool``, so the ref is an operand
of the value it names. The capability tiers come first, so ``set`` / ``erase``
/ ``on_change`` act on the slot.
"""

from __future__ import annotations

from nu.forms import Bool

from ..item import (
    ItemForm,
    ItemRef,
    MutableItemForm,
    MutableItemRef,
    ReactiveItemForm,
    ReactiveItemRef,
)


__all__ = [
    "MutablePyBoolForm",
    "MutablePyBoolRef",
    "PyBoolForm",
    "PyBoolRef",
    "ReactivePyBoolForm",
    "ReactivePyBoolRef",
]


class PyBoolForm(ItemForm, Bool):
    """Read tier of a bool slot."""


class MutablePyBoolForm(MutableItemForm, PyBoolForm):
    """Mutable tier of a bool slot: adds ``set``, ``erase`` and ``init``."""


class ReactivePyBoolForm(ReactiveItemForm, MutablePyBoolForm):
    """Reactive tier of a bool slot: adds ``on_change``."""


class PyBoolRef(ItemRef, PyBoolForm):
    """Bool slot ref, read tier."""


class MutablePyBoolRef(MutableItemRef, MutablePyBoolForm, PyBoolRef):
    """Bool slot ref, mutable tier."""


class ReactivePyBoolRef(ReactiveItemRef, ReactivePyBoolForm, MutablePyBoolRef):
    """Bool slot ref, reactive tier."""
