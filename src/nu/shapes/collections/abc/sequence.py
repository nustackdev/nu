"""Sequence collection bases - three tiers for the document model.

SequenceBase         = nu.collections.abc.SequenceBase + CollectionBase
MutableSequenceBase  = nu.collections.abc.MutableSequenceBase + MutableCollectionBase
ReactiveSequenceBase = MutableSequenceBase + ReactiveCollectionBase

Substrates implement _wrap_* methods and result() directly on their concrete refs.
"""

from __future__ import annotations

from nu.collections.abc import MutableSequenceBase as _MutableSequenceBase
from nu.collections.abc import SequenceBase as _SequenceBase

from .collection import CollectionBase, MutableCollectionBase, ReactiveCollectionBase


__all__ = [
    "MutableSequenceBase",
    "ReactiveSequenceBase",
    "SequenceBase",
]


class SequenceBase[T, CollectionValueT, ItemValueT](
    _SequenceBase[list[T], T, CollectionValueT, ItemValueT],
    CollectionBase,
):
    """Base for sequences - ordered containers in the document model."""


class MutableSequenceBase[T, CollectionValueT, ItemValueT](
    _MutableSequenceBase[list[T], T, CollectionValueT, ItemValueT],
    MutableCollectionBase[list[T]],
):
    """Mutable sequence - adds append, extend, insert, pop, remove, store, erase."""


class ReactiveSequenceBase[T, CollectionValueT, ItemValueT](
    MutableSequenceBase[T, CollectionValueT, ItemValueT],
    ReactiveCollectionBase[list[T]],
):
    """Reactive sequence - adds on_change, on_child_change, etc."""
