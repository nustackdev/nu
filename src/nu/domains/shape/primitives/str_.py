"""Str row: a leaf slot holding a ``str``, with the whole ``Str`` surface.

Two refs. ``StrRef`` is the leaf slot capability (``exists``, ``set``,
``erase``, ``init``) plus ``Str``, so the ref is an operand of the value it
names; ``ReactiveStrRef`` adds ``on_change``. The capability comes first, so
``set`` / ``erase`` / ``on_change`` act on the slot.
"""

from __future__ import annotations

from nu.forms import Str

from ..item import MutableItemRef, ReactiveItemRef


__all__ = ["ReactiveStrRef", "StrRef"]


class StrRef(MutableItemRef, Str):
    """Str slot ref."""


class ReactiveStrRef(ReactiveItemRef, StrRef):
    """Str slot ref that can be watched: adds ``on_change``."""
