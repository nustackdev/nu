"""List type — mutable sequence.

ListBase         = MutableSequenceBase (list IS mutable)
ReactiveListBase = ListBase + ViewObservable
"""

from __future__ import annotations

from everybase.abc import TypeBase
from everyshape.collections import MutableSequenceBase, ReactiveSequenceBase


__all__ = [
    "ListType",
    "ReactiveListType",
]


class ListType[T](
    MutableSequenceBase[T, object, object],
    TypeBase[list],
):
    """List — mutable sequence."""


class ReactiveListType[T](
    ListType[T],
    ReactiveSequenceBase[T, object, object],
    TypeBase[list],
):
    """Reactive list — mutable + observable."""
