"""Bytes row: a leaf slot holding a ``bytes``, with the whole ``Bytes`` surface.

Two refs. ``BytesRef`` is the leaf slot capability (``exists``, ``set``,
``erase``, ``init``) plus ``Bytes``, so the ref is an operand of the value it
names; ``ReactiveBytesRef`` adds ``on_change``. The capability comes first, so
``set`` / ``erase`` / ``on_change`` act on the slot.
"""

from __future__ import annotations

from nu.forms import Bytes

from ..item import MutableItemRef, ReactiveItemRef


__all__ = ["BytesRef", "ReactiveBytesRef"]


class BytesRef(MutableItemRef, Bytes):
    """Bytes slot ref."""


class ReactiveBytesRef(ReactiveItemRef, BytesRef):
    """Bytes slot ref that can be watched: adds ``on_change``."""
