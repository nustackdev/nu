"""Mapping collection interfaces - three tiers for the document model.

MappingForm         = nu.forms.collections.abc.MappingForm + CollectionForm
MutableMappingForm  = nu.forms.collections.abc.MutableMappingForm + MutableCollectionForm
ReactiveMappingForm = MutableMappingForm + ReactiveCollectionForm

Substrates implement _wrap_* methods and result() directly on their concrete refs.
"""

from __future__ import annotations

from nu.forms.collections.abc import MappingForm as _MappingForm
from nu.forms.collections.abc import MutableMappingForm as _MutableMappingForm

from .collection import CollectionForm, MutableCollectionForm, ReactiveCollectionForm


__all__ = [
    "MappingForm",
    "MutableMappingForm",
    "ReactiveMappingForm",
]


class MappingForm[K, V, CollectionValueT, ValueValueT](
    _MappingForm[dict[K, V], K, V, CollectionValueT, ValueValueT],
    CollectionForm,
):
    """Mapping - key-value container in the document model."""


class MutableMappingForm[K, V, CollectionValueT, ValueValueT](
    _MutableMappingForm[dict[K, V], K, V, CollectionValueT, ValueValueT],
    MutableCollectionForm[dict[K, V]],
):
    """Mutable mapping - adds set, delete, update, store, erase."""


class ReactiveMappingForm[K, V, CollectionValueT, ValueValueT](
    MutableMappingForm[K, V, CollectionValueT, ValueValueT],
    ReactiveCollectionForm[dict[K, V]],
):
    """Reactive mapping - adds on_change, on_child_change, etc."""
