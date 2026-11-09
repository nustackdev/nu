"""Bytes row: a leaf slot holding a ``bytes``, with the whole ``Bytes`` surface.

Each tier is the leaf capability tier plus ``Bytes``, so the ref is an operand
of the value it names. The capability tiers come first, so ``set`` / ``erase``
/ ``on_change`` act on the slot.
"""

from __future__ import annotations

from nu.forms import Bytes

from ..item import (
    ItemForm,
    ItemRef,
    MutableItemForm,
    MutableItemRef,
    ReactiveItemForm,
    ReactiveItemRef,
)


__all__ = [
    "MutablePyBytesForm",
    "MutablePyBytesRef",
    "PyBytesForm",
    "PyBytesRef",
    "ReactivePyBytesForm",
    "ReactivePyBytesRef",
]


class PyBytesForm(ItemForm, Bytes):
    """Read tier of a bytes slot."""


class MutablePyBytesForm(MutableItemForm, PyBytesForm):
    """Mutable tier of a bytes slot: adds ``set``, ``erase`` and ``init``."""


class ReactivePyBytesForm(ReactiveItemForm, MutablePyBytesForm):
    """Reactive tier of a bytes slot: adds ``on_change``."""


class PyBytesRef(ItemRef, PyBytesForm):
    """Bytes slot ref, read tier."""


class MutablePyBytesRef(MutableItemRef, MutablePyBytesForm, PyBytesRef):
    """Bytes slot ref, mutable tier."""


class ReactivePyBytesRef(ReactiveItemRef, ReactivePyBytesForm, MutablePyBytesRef):
    """Bytes slot ref, reactive tier."""
