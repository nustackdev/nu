"""Mapping collection interfaces - three tiers for the document model.

MappingI         = nu.collections.abc.MappingI + CollectionI
MutableMappingI  = nu.collections.abc.MutableMappingI + MutableCollectionI
ReactiveMappingI = MutableMappingI + ReactiveCollectionI

Substrates implement _wrap_* methods and result() directly on their concrete refs.
"""

from __future__ import annotations

from nu.collections.abc import MappingI as _MappingI
from nu.collections.abc import MutableMappingI as _MutableMappingI

from .collection import CollectionI, MutableCollectionI, ReactiveCollectionI


__all__ = [
    "MappingI",
    "MutableMappingI",
    "ReactiveMappingI",
]


class MappingI[K, V, CollectionValueT, ValueValueT](
    _MappingI[dict[K, V], K, V, CollectionValueT, ValueValueT],
    CollectionI,
):
    """Mapping - key-value container in the document model."""


class MutableMappingI[K, V, CollectionValueT, ValueValueT](
    _MutableMappingI[dict[K, V], K, V, CollectionValueT, ValueValueT],
    MutableCollectionI[dict[K, V]],
):
    """Mutable mapping - adds set, delete, update, store, erase."""


class ReactiveMappingI[K, V, CollectionValueT, ValueValueT](
    MutableMappingI[K, V, CollectionValueT, ValueValueT],
    ReactiveCollectionI[dict[K, V]],
):
    """Reactive mapping - adds on_change, on_child_change, etc."""
