"""List type — mutable sequence.

ListBase         = MutableSequenceBase (list IS mutable)
ReactiveListBase = ListBase + ViewObservable
"""

from __future__ import annotations

from everyshape.collections import MutableSequenceBase, ReactiveSequenceBase


__all__ = [
    "ListBase",
    "ReactiveListBase",
]


class ListBase[T](
    MutableSequenceBase[T, object, object],
):
    """List — mutable sequence."""


class ReactiveListBase[T](
    ReactiveSequenceBase[T, object, object],
    ListBase[T],
):
    """Reactive list — mutable + observable."""
