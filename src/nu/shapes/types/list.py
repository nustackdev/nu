"""List type — mutable sequence.

ListBase         = MutableSequenceBase (list IS mutable)
ReactiveListBase = ListBase + ViewObservable
"""

from __future__ import annotations

from nu.interfaces import Interface
from nu.shapes.collections import MutableSequenceBase, ReactiveSequenceBase


__all__ = [
    "ListType",
    "ReactiveListType",
]


class ListType[T](
    MutableSequenceBase[T, object, object],
    Interface[list],
):
    """List — mutable sequence."""


class ReactiveListType[T](
    ListType[T],
    ReactiveSequenceBase[T, object, object],
    Interface[list],
):
    """Reactive list — mutable + observable."""
