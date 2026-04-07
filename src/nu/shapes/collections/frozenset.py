"""FrozenSet type - immutable set.

FrozenSetType = nu.collections.abc.SetLikeBase + CollectionBase (frozenset IS immutable).

Goes directly to nu.collections.abc since shapes' SetLikeBase is set-specific.
"""

from __future__ import annotations

from nu.collections.abc import SetLikeBase as _SetLikeBase
from nu.interface import Interface

from .abc import CollectionBase


__all__ = [
    "FrozenSetType",
]


class FrozenSetType[T](
    _SetLikeBase[frozenset[T], T, object, object],
    CollectionBase,
    Interface[frozenset],
):
    """FrozenSet - immutable set."""
