"""Int row: a leaf slot holding an ``int``, with the whole ``Int`` surface.

Two refs. ``IntRef`` is the leaf slot capability (``exists``, ``set``,
``erase``, ``init``) plus ``Int``, so the ref is an operand of the value it
names; ``ReactiveIntRef`` adds ``on_change``. The capability comes first, so
``set`` / ``erase`` / ``on_change`` act on the slot.
"""

from __future__ import annotations

from nu.forms import Int

from ..item import MutableItemRef, ReactiveItemRef


__all__ = ["IntRef", "ReactiveIntRef"]


class IntRef(MutableItemRef, Int):
    """Int slot ref."""


class ReactiveIntRef(ReactiveItemRef, IntRef):
    """Int slot ref that can be watched: adds ``on_change``."""
