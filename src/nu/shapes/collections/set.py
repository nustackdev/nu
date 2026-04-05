"""Set collection bases — three tiers for the document model.

SetLikeBase     = everybase.SetLikeBase + Existable + Gettable
MutableSetBase  = everybase.MutableSetBase + Existable + Gettable + Settable + Deletable
ReactiveSetBase = MutableSetBase + ViewObservable

Substrates implement _wrap_* methods and result() directly on their concrete refs.
"""

from __future__ import annotations

from nu.interfaces import MutableSetBase as _EB_MutableSetBase
from nu.interfaces import SetLikeBase as _EB_SetLikeBase
from ..capabilities import (
    CollectionDeletableBase,
    CollectionExistableBase,
    CollectionSettableBase,
    ViewObservableBase,
)


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
):
    """Base for sets — unordered unique-element containers in the document model.

    Combines everybase set ops (union, intersection, difference, etc.)
    with everyshape capabilities (exists, get).

    Substrates implement _wrap_* and result() on their concrete refs.
    """


class MutableSetBase[T, CollectionValueT, ElementValueT](
    _EB_MutableSetBase[set[T], T, CollectionValueT, ElementValueT],
    CollectionExistableBase,
    CollectionSettableBase[set[T]],
    CollectionDeletableBase,
):
    """Mutable set — adds add, remove, discard."""


class ReactiveSetBase[T, CollectionValueT, ElementValueT](
    MutableSetBase[T, CollectionValueT, ElementValueT],
    ViewObservableBase,
):
    """Reactive set — adds on_change, on_child_change, etc."""
