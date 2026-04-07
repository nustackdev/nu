"""Set type - mutable set.

SetType         = MutableSetBase (set IS mutable)
ReactiveSetType = SetType + ReactiveCollectionBase
"""

from __future__ import annotations

from nu.interface import Interface

from .abc import MutableSetBase, ReactiveSetBase


__all__ = [
    "ReactiveSetType",
    "SetType",
]


class SetType[T](
    MutableSetBase[T, object, object],
    Interface[set],
):
    """Set - mutable set."""


class ReactiveSetType[T](
    SetType[T],
    ReactiveSetBase[T, object, object],
    Interface[set],
):
    """Reactive set - mutable + observable."""
