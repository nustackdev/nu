"""Sequence ref hierarchy — sequence bases + Ref navigation.

SequenceRefBase         = SequenceBase + Ref
MutableSequenceRefBase  = MutableSequenceBase + SequenceRefBase
ReactiveSequenceRefBase = ReactiveSequenceBase + MutableSequenceRefBase
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from everyabc import Value

from ..collections import MutableSequenceBase, ReactiveSequenceBase, SequenceBase
from .base import Ref


if TYPE_CHECKING:
    from everyabc import Sentinel, Term

    from .items import ItemRef, MutableItemRef, ReactiveItemRef


__all__ = [
    "MutableSequenceRefBase",
    "ReactiveSequenceRefBase",
    "SequenceRefBase",
]


class SequenceRefBase[T, CollectionValueT, ItemValueT: Value](
    SequenceBase[T, CollectionValueT, ItemValueT],
    Ref[list[T]],
):
    """Sequence ref — ordered container with document-model navigation."""

    @abstractmethod
    def _create_item_ref(
        self, index: int | Sentinel | Term[int | Sentinel]
    ) -> ItemRef[T, ItemValueT]:
        """Create a reference to the item at the given index."""
        ...

    def __getitem__(self, index: int | Term[int]) -> ItemRef[T, ItemValueT]:
        """Subscript access — returns a ref to the item at index."""
        return self._create_item_ref(index)


class MutableSequenceRefBase[T, CollectionValueT, ItemValueT: Value](
    MutableSequenceBase[T, CollectionValueT, ItemValueT],
    SequenceRefBase[T, CollectionValueT, ItemValueT],
):
    """Mutable sequence ref — mutations + navigation."""

    @abstractmethod
    def _create_item_ref(
        self, index: int | Sentinel | Term[int | Sentinel]
    ) -> MutableItemRef[T, ItemValueT]:
        """Create a reference to the item at the given index."""
        ...

    def __getitem__(self, index: int | Term[int]) -> MutableItemRef[T, ItemValueT]:
        """Subscript access — returns a ref to the item at index."""
        return self._create_item_ref(index)


class ReactiveSequenceRefBase[T, CollectionValueT, ItemValueT: Value](
    ReactiveSequenceBase[T, CollectionValueT, ItemValueT],
    MutableSequenceRefBase[T, CollectionValueT, ItemValueT],
):
    """Reactive sequence ref — observation + mutations + navigation."""

    @abstractmethod
    def _create_item_ref(
        self, index: int | Sentinel | Term[int | Sentinel]
    ) -> ReactiveItemRef[T, ItemValueT]:
        """Create a reference to the item at the given index."""
        ...

    def __getitem__(self, index: int | Term[int]) -> ReactiveItemRef[T, ItemValueT]:
        """Subscript access — returns a ref to the item at index."""
        return self._create_item_ref(index)
