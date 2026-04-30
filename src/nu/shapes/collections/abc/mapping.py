"""Mapping collection interfaces - three tiers for the document model.

MappingForm         = nu.forms.collections.abc.MappingForm + CollectionForm
MutableMappingForm  = nu.forms.collections.abc.MutableMappingForm + MutableCollectionI
ReactiveMappingI = MutableMappingForm + ReactiveCollectionI

Substrates implement _wrap_* methods and result() directly on their concrete refs.
"""

from __future__ import annotations

from nu.forms.collections.abc import MappingForm as _MappingI
from nu.forms.collections.abc import MutableMappingForm as _MutableMappingI

from .collection import CollectionForm, MutableCollectionI, ReactiveCollectionI


__all__ = [
    "MappingForm",
    "MutableMappingForm",
    "ReactiveMappingI",
]


class MappingForm[K, V, CollectionValueT, ValueValueT](
    _MappingI[dict[K, V], K, V, CollectionValueT, ValueValueT],
    CollectionForm,
):
    """Mapping - key-value container in the document model."""


class MutableMappingForm[K, V, CollectionValueT, ValueValueT](
    _MutableMappingI[dict[K, V], K, V, CollectionValueT, ValueValueT],
    MutableCollectionI[dict[K, V]],
):
    """Mutable mapping - adds set, delete, update, store, erase."""


class ReactiveMappingI[K, V, CollectionValueT, ValueValueT](
    MutableMappingForm[K, V, CollectionValueT, ValueValueT],
    ReactiveCollectionI[dict[K, V]],
):
    """Reactive mapping - adds on_change, on_child_change, etc."""
