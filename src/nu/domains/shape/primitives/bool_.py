"""Bool row: a leaf slot holding a ``bool``, with the whole ``Bool`` surface.

Two refs. ``BoolRef`` is the leaf slot capability (``exists``, ``set``,
``erase``, ``init``) plus ``Bool``, so the ref is an operand of the value it
names; ``ReactiveBoolRef`` adds ``on_change``. The capability comes first, so
``set`` / ``erase`` / ``on_change`` act on the slot.
"""

from __future__ import annotations

from nu.forms import Bool

from ..item import MutableItemRef, ReactiveItemRef


__all__ = ["BoolRef", "ReactiveBoolRef"]


class BoolRef(MutableItemRef, Bool):
    """Bool slot ref."""


class ReactiveBoolRef(ReactiveItemRef, BoolRef):
    """Bool slot ref that can be watched: adds ``on_change``."""
