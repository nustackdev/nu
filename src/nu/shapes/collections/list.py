"""List type - mutable sequence.

ListType         = MutableSequenceBase (list IS mutable)
ReactiveListType = ListType + ReactiveCollectionBase
"""

from __future__ import annotations

from nu.interface import Interface

from .abc import MutableSequenceBase, ReactiveSequenceBase


__all__ = [
    "ListType",
    "ReactiveListType",
]


class ListType[T](
    MutableSequenceBase[T, object, object],
    Interface[list],
):
    """List - mutable sequence."""


class ReactiveListType[T](
    ListType[T],
    ReactiveSequenceBase[T, object, object],
    Interface[list],
):
    """Reactive list - mutable + observable."""
