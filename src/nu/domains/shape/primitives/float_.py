"""Float row: a leaf slot holding a ``float``, with the whole ``Float`` surface.

Each tier is the leaf capability tier plus ``Float``, so the ref is an operand
of the value it names. The capability tiers come first, so ``set`` / ``erase``
/ ``on_change`` act on the slot.
"""

from __future__ import annotations

from nu.forms import Float

from ..item import (
    ItemForm,
    ItemRef,
    MutableItemForm,
    MutableItemRef,
    ReactiveItemForm,
    ReactiveItemRef,
)


__all__ = [
    "MutablePyFloatForm",
    "MutablePyFloatRef",
    "PyFloatForm",
    "PyFloatRef",
    "ReactivePyFloatForm",
    "ReactivePyFloatRef",
]


class PyFloatForm(ItemForm, Float):
    """Read tier of a float slot."""


class MutablePyFloatForm(MutableItemForm, PyFloatForm):
    """Mutable tier of a float slot: adds ``set``, ``erase`` and ``init``."""


class ReactivePyFloatForm(ReactiveItemForm, MutablePyFloatForm):
    """Reactive tier of a float slot: adds ``on_change``."""


class PyFloatRef(ItemRef, PyFloatForm):
    """Float slot ref, read tier."""


class MutablePyFloatRef(MutableItemRef, MutablePyFloatForm, PyFloatRef):
    """Float slot ref, mutable tier."""


class ReactivePyFloatRef(ReactiveItemRef, ReactivePyFloatForm, MutablePyFloatRef):
    """Float slot ref, reactive tier."""
