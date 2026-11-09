"""Int row: a leaf slot holding an ``int``, with the whole ``Int`` surface.

Each tier is the leaf capability tier plus ``Int``, so the ref is an operand
of the value it names. The capability tiers come first, so ``set`` / ``erase``
/ ``on_change`` act on the slot.
"""

from __future__ import annotations

from nu.forms import Int

from ..item import (
    ItemForm,
    ItemRef,
    MutableItemForm,
    MutableItemRef,
    ReactiveItemForm,
    ReactiveItemRef,
)


__all__ = [
    "MutablePyIntForm",
    "MutablePyIntRef",
    "PyIntForm",
    "PyIntRef",
    "ReactivePyIntForm",
    "ReactivePyIntRef",
]


class PyIntForm(ItemForm, Int):
    """Read tier of an int slot."""


class MutablePyIntForm(MutableItemForm, PyIntForm):
    """Mutable tier of an int slot: adds ``set``, ``erase`` and ``init``."""


class ReactivePyIntForm(ReactiveItemForm, MutablePyIntForm):
    """Reactive tier of an int slot: adds ``on_change``."""


class PyIntRef(ItemRef, PyIntForm):
    """Int slot ref, read tier."""


class MutablePyIntRef(MutableItemRef, MutablePyIntForm, PyIntRef):
    """Int slot ref, mutable tier."""


class ReactivePyIntRef(ReactiveItemRef, ReactivePyIntForm, MutablePyIntRef):
    """Int slot ref, reactive tier."""
