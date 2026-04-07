"""Shaped ListI - the complete document-model list.

Mutable, reactive, collection-aware.
"""

from __future__ import annotations

from nu.interface import Interface

from .abc import ReactiveSequenceI


__all__ = [
    "ListI",
]


class ListI[T](
    ReactiveSequenceI[T, object, object],
    Interface[list],
):
    """Shaped list - reactive mutable sequence with collection ops."""
