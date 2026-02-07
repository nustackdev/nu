"""Mapping collection bases — three tiers for the document model.

MappingBase         = everybase.MappingBase + Existable + Extractable
MutableMappingBase  = everybase.MutableMappingBase + MappingBase + Lengthable + Clearable + Storable
ReactiveMappingBase = MutableMappingBase + ViewObservable

Substrates implement _wrap_* methods and result() directly on their concrete refs.
"""

from __future__ import annotations

from eb_shape.capabilities import (
    CollectionExistableBase,
    CollectionExtractableBase,
    CollectionStorableBase,
    ViewObservableBase,
)
from everybase.abc import MappingBase as _EB_MappingBase
from everybase.abc import MutableMappingBase as _EB_MutableMappingBase


__all__ = [
    "MappingBase",
    "MutableMappingBase",
    "ReactiveMappingBase",
]


# =============================================================================
# MAPPING — three tiers
# =============================================================================


class MappingBase[K, V, CollectionValueT, ValueValueT](
    _EB_MappingBase[dict[K, V], K, V, CollectionValueT, ValueValueT],
    CollectionExistableBase,
    CollectionExtractableBase[CollectionValueT],
):
    """Base for mappings — key-value containers in the document model.

    Combines everybase mapping ops (keys_, values_, items_, get_, set_, etc.)
    with eb_shape capabilities (exists, get/extract).

    Substrates implement _wrap_* and result() on their concrete refs.
    """


class MutableMappingBase[K, V, CollectionValueT, ValueValueT](
    _EB_MutableMappingBase[dict[K, V], K, V, CollectionValueT, ValueValueT],
    CollectionExistableBase,
    CollectionExtractableBase[CollectionValueT],
    CollectionStorableBase[CollectionValueT, dict[K, V]],
):
    """Mutable mapping — adds set_, delete, update_."""


class ReactiveMappingBase[K, V, CollectionValueT, ValueValueT](
    MutableMappingBase[K, V, CollectionValueT, ValueValueT],
    ViewObservableBase,
):
    """Reactive mapping — adds on_change, on_child_change, etc."""
