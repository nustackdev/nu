"""Sequence collection interfaces - three tiers for the document model.

SequenceI         = nu.collections.abc.SequenceI + CollectionI
MutableSequenceI  = nu.collections.abc.MutableSequenceI + MutableCollectionI
ReactiveSequenceI = MutableSequenceI + ReactiveCollectionI

Substrates implement _wrap_* methods and result() directly on their concrete refs.
"""

from __future__ import annotations

from nu.collections.abc import MutableSequenceI as _MutableSequenceI
from nu.collections.abc import SequenceI as _SequenceI

from .collection import CollectionI, MutableCollectionI, ReactiveCollectionI


__all__ = [
    "MutableSequenceI",
    "ReactiveSequenceI",
    "SequenceI",
]


class SequenceI[T, CollectionValueT, ItemValueT](
    _SequenceI[list[T], T, CollectionValueT, ItemValueT],
    CollectionI,
):
    """Sequence - ordered container in the document model."""


class MutableSequenceI[T, CollectionValueT, ItemValueT](
    _MutableSequenceI[list[T], T, CollectionValueT, ItemValueT],
    MutableCollectionI[list[T]],
):
    """Mutable sequence - adds append, extend, insert, pop, remove, store, erase."""


class ReactiveSequenceI[T, CollectionValueT, ItemValueT](
    MutableSequenceI[T, CollectionValueT, ItemValueT],
    ReactiveCollectionI[list[T]],
):
    """Reactive sequence - adds on_change, on_child_change, etc."""
