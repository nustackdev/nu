"""Mapping ref hierarchy — mapping bases + Ref navigation.

MappingRef         = MappingI + Ref
MutableMappingRef  = MutableMappingI + MappingRef
ReactiveMappingRef = ReactiveMappingI + MutableMappingRef

Type Parameters:
    K:              Native key type (str, int, etc.)
    V:              Native value type (int, str, dict[str, object], etc.)
    CollectionValueT: Wrapped result for collection-level ops (extract, store)
    ValueValueT:     Wrapped result for value-level ops (get, set) — Value subclass
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from nu.shapes.collections import MappingI, MutableMappingI, ReactiveMappingI

from .base import Ref


if TYPE_CHECKING:
    from nu import Arg, Sentinel

    from .item import ItemRef, MutableItemRef, ReactiveItemRef


__all__ = [
    "MappingRef",
    "MutableMappingRef",
    "ReactiveMappingRef",
]


class MappingRef[K, V, CollectionValueT, ValueValueT](
    MappingI[K, V, CollectionValueT, ValueValueT],
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


class MutableMappingRef[K, V, CollectionValueT, ValueValueT](
    MutableMappingI[K, V, CollectionValueT, ValueValueT],
    MappingRef[K, V, CollectionValueT, ValueValueT],
):
    """Mutable mapping ref — mutations + navigation."""

    @abstractmethod
    def _create_child_ref(self, key: Arg[K] | Sentinel) -> MutableItemRef[V, ValueValueT]:
        """Create a reference to the value at the given key."""
        ...

    def __getitem__(self, key: Arg[K]) -> MutableItemRef[V, ValueValueT]:
        """Subscript access — returns a ref to the value at key."""
        return self._create_child_ref(key)


class ReactiveMappingRef[K, V, CollectionValueT, ValueValueT](
    ReactiveMappingI[K, V, CollectionValueT, ValueValueT],
    MutableMappingRef[K, V, CollectionValueT, ValueValueT],
):
    """Reactive mapping ref — observation + mutations + navigation."""

    @abstractmethod
    def _create_child_ref(self, key: Arg[K] | Sentinel) -> ReactiveItemRef[V, ValueValueT]:
        """Create a reference to the value at the given key."""
        ...

    def __getitem__(self, key: Arg[K]) -> ReactiveItemRef[V, ValueValueT]:
        """Subscript access — returns a ref to the value at key."""
        return self._create_child_ref(key)
