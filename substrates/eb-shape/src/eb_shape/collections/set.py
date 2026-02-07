"""Set collection bases — three tiers for the document model.

SetLikeBase     = everybase.SetLikeBase + Existable + Extractable
MutableSetBase  = everybase.MutableSetBase + Existable + Extractable + Storable
ReactiveSetBase = MutableSetBase + ViewObservable

Substrates implement _wrap_* methods and result() directly on their concrete refs.
"""

from __future__ import annotations

from eb_shape.capabilities import (
    CollectionExistableBase,
    CollectionExtractableBase,
    CollectionStorableBase,
    ViewObservableBase,
)
from everybase.abc import MutableSetBase as _EB_MutableSetBase
from everybase.abc import SetLikeBase as _EB_SetLikeBase


__all__ = [
    "MutableSetBase",
    "ReactiveSetBase",
    "SetLikeBase",
]


# =============================================================================
# SET — three tiers
# =============================================================================


class SetLikeBase[T, CollectionValueT, ElementValueT](
    _EB_SetLikeBase[set[T], T, CollectionValueT, ElementValueT],
    CollectionExistableBase,
    CollectionExtractableBase[CollectionValueT],
):
    """Base for sets — unordered unique-element containers in the document model.

    Combines everybase set ops (union, intersection, difference, etc.)
    with eb_shape capabilities (exists, extract).

    Substrates implement _wrap_* and result() on their concrete refs.
    """


class MutableSetBase[T, CollectionValueT, ElementValueT](
    _EB_MutableSetBase[set[T], T, CollectionValueT, ElementValueT],
    CollectionExistableBase,
    CollectionExtractableBase[CollectionValueT],
    CollectionStorableBase[CollectionValueT, set[T]],
):
    """Mutable set — adds add, remove, discard."""


class ReactiveSetBase[T, CollectionValueT, ElementValueT](
    MutableSetBase[T, CollectionValueT, ElementValueT],
    ViewObservableBase,
):
    """Reactive set — adds on_change, on_child_change, etc."""
