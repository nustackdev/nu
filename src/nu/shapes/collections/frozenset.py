"""Shaped FrozenSetI - immutable set in the document model.

Goes directly to nu.collections.abc since shapes' SetLikeI is set-specific.
"""

from __future__ import annotations

from nu.collections.abc import SetLikeI as _SetLikeI
from nu.interface import Interface

from .abc import CollectionI


__all__ = [
    "FrozenSetI",
]


class FrozenSetI[T](
    _SetLikeI[frozenset[T], T, object, object],
    CollectionI,
    Interface[frozenset],
):
    """Shaped frozenset - immutable set with collection ops."""
