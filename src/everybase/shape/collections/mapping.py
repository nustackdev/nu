"""Mapping collection bases — three tiers for the document model.

MappingBase         = everybase.MappingBase + Existable + Gettable
MutableMappingBase  = everybase.MutableMappingBase + MappingBase + Lengthable + Settable + Deletable
ReactiveMappingBase = MutableMappingBase + ViewObservable

Substrates implement _wrap_* methods and result() directly on their concrete refs.
"""

from __future__ import annotations

from everybase.abc import MappingBase as _EB_MappingBase
from everybase.abc import MutableMappingBase as _EB_MutableMappingBase
from everybase.shape.capabilities import (
    CollectionDeletableBase,
    CollectionExistableBase,
    CollectionSettableBase,
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
):
    """Base for mappings — key-value containers in the document model.

    Combines everybase mapping ops (keys, values, items, get, set, etc.)
    with everyshape capabilities (exists, get).

    Substrates implement _wrap_* and result() on their concrete refs.
    """


class MutableMappingBase[K, V, CollectionValueT, ValueValueT](
    _EB_MutableMappingBase[dict[K, V], K, V, CollectionValueT, ValueValueT],
    CollectionExistableBase,
    CollectionSettableBase[CollectionValueT, dict[K, V]],
    CollectionDeletableBase,
):
    """Mutable mapping — adds set, delete, update."""


class ReactiveMappingBase[K, V, CollectionValueT, ValueValueT](
    MutableMappingBase[K, V, CollectionValueT, ValueValueT],
    ViewObservableBase,
):
    """Reactive mapping — adds on_change, on_child_change, etc."""
