"""List type — mutable sequence.

ListBase         = MutableSequenceBase (list IS mutable)
ReactiveListBase = ListBase + ViewObservable
"""

from __future__ import annotations

from nu.abc import Object
from nu.shape.collections import MutableSequenceBase, ReactiveSequenceBase


__all__ = [
    "ListType",
    "ReactiveListType",
]


class ListType[T](
    MutableSequenceBase[T, object, object],
    Object[list],
):
    """List — mutable sequence."""


class ReactiveListType[T](
    ListType[T],
    ReactiveSequenceBase[T, object, object],
    Object[list],
):
    """Reactive list — mutable + observable."""
