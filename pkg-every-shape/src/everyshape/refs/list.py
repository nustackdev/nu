"""Sequence ref hierarchy — sequence bases + Ref navigation.

SequenceRefBase         = SequenceBase + Ref
MutableSequenceRefBase  = MutableSequenceBase + SequenceRefBase
ReactiveSequenceRefBase = ReactiveSequenceBase + MutableSequenceRefBase
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from everybase import Value
from everyshape.collections import MutableSequenceBase, ReactiveSequenceBase, SequenceBase

from .base import Ref


if TYPE_CHECKING:
    from everybase import IntArg, Sentinel

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
    def _create_item_ref(self, index: IntArg | Sentinel) -> ItemRef[T, ItemValueT]:
        """Create a reference to the item at the given index."""
        ...

    def __getitem__(self, index: IntArg) -> ItemRef[T, ItemValueT]:
        """Subscript access — returns a ref to the item at index."""
        return self._create_item_ref(index)


class MutableSequenceRefBase[T, CollectionValueT, ItemValueT: Value](
    MutableSequenceBase[T, CollectionValueT, ItemValueT],
    Ref[list[T]],
):
    """Mutable sequence ref — mutations + navigation."""

    @abstractmethod
    def _create_item_ref(self, index: IntArg | Sentinel) -> MutableItemRef[T, ItemValueT]:
        """Create a reference to the item at the given index."""
        ...

    def __getitem__(self, index: IntArg) -> MutableItemRef[T, ItemValueT]:
        """Subscript access — returns a ref to the item at index."""
        return self._create_item_ref(index)


class ReactiveSequenceRefBase[T, CollectionValueT, ItemValueT: Value](
    ReactiveSequenceBase[T, CollectionValueT, ItemValueT],
    Ref[list[T]],
):
    """Reactive sequence ref — observation + mutations + navigation."""

    @abstractmethod
    def _create_item_ref(self, index: IntArg | Sentinel) -> ReactiveItemRef[T, ItemValueT]:
        """Create a reference to the item at the given index."""
        ...

    def __getitem__(self, index: IntArg) -> ReactiveItemRef[T, ItemValueT]:
        """Subscript access — returns a ref to the item at index."""
        return self._create_item_ref(index)
