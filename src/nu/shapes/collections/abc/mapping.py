"""Mapping collection bases - three tiers for the document model.

MappingBase         = nu.collections.abc.MappingBase + CollectionBase
MutableMappingBase  = nu.collections.abc.MutableMappingBase + MutableCollectionBase
ReactiveMappingBase = MutableMappingBase + ReactiveCollectionBase

Substrates implement _wrap_* methods and result() directly on their concrete refs.
"""

from __future__ import annotations

from nu.collections.abc import MappingBase as _MappingBase
from nu.collections.abc import MutableMappingBase as _MutableMappingBase

from .collection import CollectionBase, MutableCollectionBase, ReactiveCollectionBase


__all__ = [
    "MappingBase",
    "MutableMappingBase",
    "ReactiveMappingBase",
]


class MappingBase[K, V, CollectionValueT, ValueValueT](
    _MappingBase[dict[K, V], K, V, CollectionValueT, ValueValueT],
    CollectionBase,
):
    """Base for mappings - key-value containers in the document model."""


class MutableMappingBase[K, V, CollectionValueT, ValueValueT](
    _MutableMappingBase[dict[K, V], K, V, CollectionValueT, ValueValueT],
    MutableCollectionBase[dict[K, V]],
):
    """Mutable mapping - adds set, delete, update, store, erase."""


class ReactiveMappingBase[K, V, CollectionValueT, ValueValueT](
    MutableMappingBase[K, V, CollectionValueT, ValueValueT],
    ReactiveCollectionBase[dict[K, V]],
):
    """Reactive mapping - adds on_change, on_child_change, etc."""
