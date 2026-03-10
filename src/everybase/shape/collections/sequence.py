"""Sequence collection bases — three tiers for the document model.

SequenceBase         = everybase.SequenceBase + Existable + Gettable
MutableSequenceBase  = everybase.MutableSequenceBase + SequenceBase + Lengthable + Settable + Deletable
ReactiveSequenceBase = MutableSequenceBase + ViewObservable

Substrates implement _wrap_* methods and result() directly on their concrete refs.
"""

from __future__ import annotations

from everybase.abc import MutableSequenceBase as _EB_MutableSequenceBase
from everybase.abc import SequenceBase as _EB_SequenceBase
from everybase.shape.capabilities import (
    CollectionDeletableBase,
    CollectionExistableBase,
    CollectionSettableBase,
    ViewObservableBase,
)


__all__ = [
    "MutableSequenceBase",
    "ReactiveSequenceBase",
    "SequenceBase",
]


# =============================================================================
# SEQUENCE — three tiers
# =============================================================================


class SequenceBase[T, CollectionValueT, ItemValueT](
    _EB_SequenceBase[list[T], T, CollectionValueT, ItemValueT],
    CollectionExistableBase,
):
    """Base for sequences — ordered containers in the document model.

    Combines everybase sequence ops (map_, filter_, first, last, etc.)
    with everyshape capabilities (exists, get).

    Substrates implement _wrap_* and result() on their concrete refs.
    """


class MutableSequenceBase[T, CollectionValueT, ItemValueT](
    _EB_MutableSequenceBase[list[T], T, CollectionValueT, ItemValueT],
    CollectionExistableBase,
    CollectionSettableBase[CollectionValueT, list[T]],
    CollectionDeletableBase,
):
    """Mutable sequence — adds append, extend, insert, pop, remove."""


class ReactiveSequenceBase[T, CollectionValueT, ItemValueT](
    MutableSequenceBase[T, CollectionValueT, ItemValueT],
    ViewObservableBase,
):
    """Reactive sequence — adds on_change, on_child_change, etc."""
