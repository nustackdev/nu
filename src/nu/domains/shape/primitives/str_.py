"""Str row: a leaf slot holding a ``str``, with the whole ``Str`` surface.

Each tier is the leaf capability tier plus ``Str``, so the ref is an operand
of the value it names. The capability tiers come first, so ``set`` / ``erase``
/ ``on_change`` act on the slot.
"""

from __future__ import annotations

from nu.forms import Str

from ..item import (
    ItemForm,
    ItemRef,
    MutableItemForm,
    MutableItemRef,
    ReactiveItemForm,
    ReactiveItemRef,
)


__all__ = [
    "MutablePyStrForm",
    "MutablePyStrRef",
    "PyStrForm",
    "PyStrRef",
    "ReactivePyStrForm",
    "ReactivePyStrRef",
]


class PyStrForm(ItemForm, Str):
    """Read tier of a str slot."""


class MutablePyStrForm(MutableItemForm, PyStrForm):
    """Mutable tier of a str slot: adds ``set``, ``erase`` and ``init``."""


class ReactivePyStrForm(ReactiveItemForm, MutablePyStrForm):
    """Reactive tier of a str slot: adds ``on_change``."""


class PyStrRef(ItemRef, PyStrForm):
    """Str slot ref, read tier."""


class MutablePyStrRef(MutableItemRef, MutablePyStrForm, PyStrRef):
    """Str slot ref, mutable tier."""


class ReactivePyStrRef(ReactiveItemRef, ReactivePyStrForm, MutablePyStrRef):
    """Str slot ref, reactive tier."""
