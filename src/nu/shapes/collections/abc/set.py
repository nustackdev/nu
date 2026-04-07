"""Set collection bases - three tiers for the document model.

SetLikeBase     = nu.collections.abc.SetLikeBase + CollectionBase
MutableSetBase  = nu.collections.abc.MutableSetBase + MutableCollectionBase
ReactiveSetBase = MutableSetBase + ReactiveCollectionBase

Substrates implement _wrap_* methods and result() directly on their concrete refs.
"""

from __future__ import annotations

from nu.collections.abc import MutableSetBase as _MutableSetBase
from nu.collections.abc import SetLikeBase as _SetLikeBase

from .collection import CollectionBase, MutableCollectionBase, ReactiveCollectionBase


__all__ = [
    "MutableSetBase",
    "ReactiveSetBase",
    "SetLikeBase",
]


class SetLikeBase[T, CollectionValueT, ElementValueT](
    _SetLikeBase[set[T], T, CollectionValueT, ElementValueT],
    CollectionBase,
):
    """Base for sets - unordered unique-element containers in the document model."""


class MutableSetBase[T, CollectionValueT, ElementValueT](
    _MutableSetBase[set[T], T, CollectionValueT, ElementValueT],
    MutableCollectionBase[set[T]],
):
    """Mutable set - adds add, remove, discard, store, erase."""


class ReactiveSetBase[T, CollectionValueT, ElementValueT](
    MutableSetBase[T, CollectionValueT, ElementValueT],
    ReactiveCollectionBase[set[T]],
):
    """Reactive set - adds on_change, on_child_change, etc."""
