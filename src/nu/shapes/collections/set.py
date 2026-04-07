"""Shaped SetI - the complete document-model set.

Mutable, reactive, collection-aware.
"""

from __future__ import annotations

from nu.interface import Interface

from .abc import ReactiveSetI


__all__ = [
    "SetI",
]


class SetI[T](
    ReactiveSetI[T, object, object],
    Interface[set],
):
    """Shaped set - reactive mutable set with collection ops."""
