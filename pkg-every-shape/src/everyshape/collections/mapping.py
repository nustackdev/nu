"""Mapping collection bases — three tiers for the document model.

MappingBase         = everybase.MappingBase + Existable + Extractable
MutableMappingBase  = everybase.MutableMappingBase + MappingBase + Lengthable + Clearable + Storable
ReactiveMappingBase = MutableMappingBase + ViewObservable

Substrates implement _wrap_* methods and result() directly on their concrete refs.
"""

from __future__ import annotations

from everybase.collections import MappingBase as _EB_MappingBase
from everybase.collections import MutableMappingBase as _EB_MutableMappingBase
from everyshape.capabilities import (
    CollectionClearableBase,
    CollectionExistableBase,
    CollectionExtractableBase,
    CollectionLengthableBase,
    CollectionStorableBase,
    ViewObservableBase,
)


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
    with everyshape capabilities (exists, get/extract).

    Substrates implement _wrap_* and result() on their concrete refs.
    """


class MutableMappingBase[K, V, CollectionValueT, ValueValueT](
    _EB_MutableMappingBase[dict[K, V], K, V, CollectionValueT, ValueValueT],
    MappingBase[K, V, CollectionValueT, ValueValueT],
    CollectionLengthableBase,
    CollectionClearableBase,
    CollectionStorableBase[CollectionValueT, dict[K, V]],
):
    """Mutable mapping — adds set_, delete, update_.

    Also adds length(), clear(), store() from everyshape capabilities.
    Diamond at _EB_MappingBase resolved by C3 linearization.
    """


class ReactiveMappingBase[K, V, CollectionValueT, ValueValueT](
    MutableMappingBase[K, V, CollectionValueT, ValueValueT],
    ViewObservableBase,
):
    """Reactive mapping — adds on_change, on_child_change, etc."""
