"""Set collection interfaces - three tiers for the document model.

SetLikeI     = nu.collections.abc.SetLikeBase + CollectionI
MutableSetI  = nu.collections.abc.MutableSetBase + MutableCollectionI
ReactiveSetI = MutableSetI + ReactiveCollectionI

Substrates implement _wrap_* methods and result() directly on their concrete refs.
"""

from __future__ import annotations

from nu.collections.abc import MutableSetBase as _MutableSetBase
from nu.collections.abc import SetLikeBase as _SetLikeBase

from .collection import CollectionI, MutableCollectionI, ReactiveCollectionI


__all__ = [
    "MutableSetI",
    "ReactiveSetI",
    "SetLikeI",
]


class SetLikeI[T, CollectionValueT, ElementValueT](
    _SetLikeBase[set[T], T, CollectionValueT, ElementValueT],
    CollectionI,
):
    """Set - unordered unique-element container in the document model."""


class MutableSetI[T, CollectionValueT, ElementValueT](
    _MutableSetBase[set[T], T, CollectionValueT, ElementValueT],
    MutableCollectionI[set[T]],
):
    """Mutable set - adds add, remove, discard, store, erase."""


class ReactiveSetI[T, CollectionValueT, ElementValueT](
    MutableSetI[T, CollectionValueT, ElementValueT],
    ReactiveCollectionI[set[T]],
):
    """Reactive set - adds on_change, on_child_change, etc."""
