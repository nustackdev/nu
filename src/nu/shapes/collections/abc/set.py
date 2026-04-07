"""Set collection interfaces - three tiers for the document model.

SetLikeI     = nu.collections.abc.SetLikeI + CollectionI
MutableSetI  = nu.collections.abc.MutableSetI + MutableCollectionI
ReactiveSetI = MutableSetI + ReactiveCollectionI

Substrates implement _wrap_* methods and result() directly on their concrete refs.
"""

from __future__ import annotations

from nu.collections.abc import MutableSetI as _MutableSetI
from nu.collections.abc import SetLikeI as _SetLikeI

from .collection import CollectionI, MutableCollectionI, ReactiveCollectionI


__all__ = [
    "MutableSetI",
    "ReactiveSetI",
    "SetLikeI",
]


class SetLikeI[T, CollectionValueT, ElementValueT](
    _SetLikeI[set[T], T, CollectionValueT, ElementValueT],
    CollectionI,
):
    """Set - unordered unique-element container in the document model."""


class MutableSetI[T, CollectionValueT, ElementValueT](
    _MutableSetI[set[T], T, CollectionValueT, ElementValueT],
    MutableCollectionI[set[T]],
):
    """Mutable set - adds add, remove, discard, store, erase."""


class ReactiveSetI[T, CollectionValueT, ElementValueT](
    MutableSetI[T, CollectionValueT, ElementValueT],
    ReactiveCollectionI[set[T]],
):
    """Reactive set - adds on_change, on_child_change, etc."""
