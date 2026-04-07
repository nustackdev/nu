"""Mapping collection interfaces - three tiers for the document model.

MappingI         = nu.collections.abc.MappingBase + CollectionI
MutableMappingI  = nu.collections.abc.MutableMappingBase + MutableCollectionI
ReactiveMappingI = MutableMappingI + ReactiveCollectionI

Substrates implement _wrap_* methods and result() directly on their concrete refs.
"""

from __future__ import annotations

from nu.collections.abc import MappingBase as _MappingBase
from nu.collections.abc import MutableMappingBase as _MutableMappingBase

from .collection import CollectionI, MutableCollectionI, ReactiveCollectionI


__all__ = [
    "MappingI",
    "MutableMappingI",
    "ReactiveMappingI",
]


class MappingI[K, V, CollectionValueT, ValueValueT](
    _MappingBase[dict[K, V], K, V, CollectionValueT, ValueValueT],
    CollectionI,
):
    """Mapping - key-value container in the document model."""


class MutableMappingI[K, V, CollectionValueT, ValueValueT](
    _MutableMappingBase[dict[K, V], K, V, CollectionValueT, ValueValueT],
    MutableCollectionI[dict[K, V]],
):
    """Mutable mapping - adds set, delete, update, store, erase."""


class ReactiveMappingI[K, V, CollectionValueT, ValueValueT](
    MutableMappingI[K, V, CollectionValueT, ValueValueT],
    ReactiveCollectionI[dict[K, V]],
):
    """Reactive mapping - adds on_change, on_child_change, etc."""
