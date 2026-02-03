"""Mapping ref hierarchy — mapping bases + Ref navigation.

MappingRefBase         = MappingBase + Ref
MutableMappingRefBase  = MutableMappingBase + MappingRefBase
ReactiveMappingRefBase = ReactiveMappingBase + MutableMappingRefBase
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from everyabc import Value
from everyshape.collections import MappingBase, MutableMappingBase, ReactiveMappingBase

from .base import Ref


if TYPE_CHECKING:
    from everyabc import Arg, Sentinel

    from .items import ItemRef, MutableItemRef, ReactiveItemRef


__all__ = [
    "MappingRefBase",
    "MutableMappingRefBase",
    "ReactiveMappingRefBase",
]


class MappingRefBase[K, V, CollectionValueT, ValueValueT: Value](
    MappingBase[K, V, CollectionValueT, ValueValueT],
    Ref[dict[K, V]],
):
    """Mapping ref — key-value container with document-model navigation."""

    @abstractmethod
    def _create_child_ref(self, key: Arg[K] | Sentinel) -> ItemRef[V, ValueValueT]:
        """Create a reference to the value at the given key."""
        ...

    def __getitem__(self, key: Arg[K]) -> ItemRef[V, ValueValueT]:
        """Subscript access — returns a ref to the value at key."""
        return self._create_child_ref(key)


class MutableMappingRefBase[K, V, CollectionValueT, ValueValueT: Value](
    MutableMappingBase[K, V, CollectionValueT, ValueValueT],
    MappingRefBase[K, V, CollectionValueT, ValueValueT],
):
    """Mutable mapping ref — mutations + navigation."""

    @abstractmethod
    def _create_child_ref(self, key: Arg[K] | Sentinel) -> MutableItemRef[V, ValueValueT]:
        """Create a reference to the value at the given key."""
        ...

    def __getitem__(self, key: Arg[K]) -> MutableItemRef[V, ValueValueT]:
        """Subscript access — returns a ref to the value at key."""
        return self._create_child_ref(key)


class ReactiveMappingRefBase[K, V, CollectionValueT, ValueValueT: Value](
    ReactiveMappingBase[K, V, CollectionValueT, ValueValueT],
    MutableMappingRefBase[K, V, CollectionValueT, ValueValueT],
):
    """Reactive mapping ref — observation + mutations + navigation."""

    @abstractmethod
    def _create_child_ref(self, key: Arg[K] | Sentinel) -> ReactiveItemRef[V, ValueValueT]:
        """Create a reference to the value at the given key."""
        ...

    def __getitem__(self, key: Arg[K]) -> ReactiveItemRef[V, ValueValueT]:
        """Subscript access — returns a ref to the value at key."""
        return self._create_child_ref(key)
