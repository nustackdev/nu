"""Float row: a leaf slot holding a ``float``, with the whole ``Float`` surface.

Two refs. ``FloatRef`` is the leaf slot capability (``exists``, ``set``,
``erase``, ``init``) plus ``Float``, so the ref is an operand of the value it
names; ``ReactiveFloatRef`` adds ``on_change``. The capability comes first, so
``set`` / ``erase`` / ``on_change`` act on the slot.
"""

from __future__ import annotations

from nu.surfaces import FloatSurface

from ..item import MutableItemRef, ReactiveItemRef


__all__ = ["FloatRef", "ReactiveFloatRef"]


class FloatRef(MutableItemRef, FloatSurface):
    """Float slot ref."""


class ReactiveFloatRef(ReactiveItemRef, FloatRef):
    """Float slot ref that can be watched: adds ``on_change``."""
