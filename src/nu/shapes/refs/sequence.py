"""Sequence ref hierarchy — sequence bases + Ref navigation.

SequenceRef         = SequenceI + Ref
MutableSequenceRef  = MutableSequenceI + Ref
ReactiveSequenceRef = ReactiveSequenceI + Ref

Type Parameters:
    T:               Native element type (int, str, etc.)
    CollectionValueT: Wrapped result for collection-level ops (get, set)
    ItemValueT:       Wrapped result for item-level ops (get, set) — Value subclass
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from nu.shapes.collections import MutableSequenceI, ReactiveSequenceI, SequenceI
from .base import Ref


if TYPE_CHECKING:
    from nu import IntArg, Sentinel

    from .item import ItemRef, MutableItemRef, ReactiveItemRef


__all__ = [
    "MutableSequenceRef",
    "ReactiveSequenceRef",
    "SequenceRef",
]


class SequenceRef[T, CollectionValueT, ItemValueT](
    SequenceI[T, CollectionValueT, ItemValueT],
    Ref[list[T]],
):
    """Sequence ref — ordered container with document-model navigation."""

    @abstractmethod
    def _create_item_ref(self, index: IntArg | Sentinel) -> ItemRef[T, ItemValueT]:
        """Create a reference to the item at the given index."""
        ...

    def __getitem__(self, index: IntArg) -> ItemRef[T, ItemValueT]:
        """Subscript access — returns a ref to the item at index."""
        return self._create_item_ref(index)


class MutableSequenceRef[T, CollectionValueT, ItemValueT](
    MutableSequenceI[T, CollectionValueT, ItemValueT],
    SequenceRef[T, CollectionValueT, ItemValueT],
):
    """Mutable sequence ref — mutations + navigation."""

    @abstractmethod
    def _create_item_ref(self, index: IntArg | Sentinel) -> MutableItemRef[T, ItemValueT]:
        """Create a reference to the item at the given index."""
        ...

    def __getitem__(self, index: IntArg) -> MutableItemRef[T, ItemValueT]:
        """Subscript access — returns a ref to the item at index."""
        return self._create_item_ref(index)


class ReactiveSequenceRef[T, CollectionValueT, ItemValueT](
    ReactiveSequenceI[T, CollectionValueT, ItemValueT],
    MutableSequenceRef[T, CollectionValueT, ItemValueT],
):
    """Reactive sequence ref — observation + mutations + navigation."""

    @abstractmethod
    def _create_item_ref(self, index: IntArg | Sentinel) -> ReactiveItemRef[T, ItemValueT]:
        """Create a reference to the item at the given index."""
        ...

    def __getitem__(self, index: IntArg) -> ReactiveItemRef[T, ItemValueT]:
        """Subscript access — returns a ref to the item at index."""
        return self._create_item_ref(index)
