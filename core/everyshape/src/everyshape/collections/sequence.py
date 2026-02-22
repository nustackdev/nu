"""Sequence collection bases — three tiers for the document model.

SequenceBase         = everybase.SequenceBase + Existable + Extractable
MutableSequenceBase  = everybase.MutableSequenceBase + SequenceBase + Lengthable + Clearable + Storable
ReactiveSequenceBase = MutableSequenceBase + ViewObservable

Substrates implement _wrap_* methods and result() directly on their concrete refs.
"""

from __future__ import annotations

from everybase.abc import MutableSequenceBase as _EB_MutableSequenceBase
from everybase.abc import SequenceBase as _EB_SequenceBase
from everyshape.capabilities import (
    CollectionExistableBase,
    CollectionExtractableBase,
    CollectionInitializableBase,
    CollectionStorableBase,
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
    CollectionExtractableBase[CollectionValueT],
):
    """Base for sequences — ordered containers in the document model.

    Combines everybase sequence ops (map_, filter_, first, last, etc.)
    with everyshape capabilities (exists, get/extract).

    Substrates implement _wrap_* and result() on their concrete refs.
    """


class MutableSequenceBase[T, CollectionValueT, ItemValueT](
    _EB_MutableSequenceBase[list[T], T, CollectionValueT, ItemValueT],
    CollectionExistableBase,
    CollectionExtractableBase[CollectionValueT],
    CollectionInitializableBase,
    CollectionStorableBase[CollectionValueT, list[T]],
):
    """Mutable sequence — adds append, extend, insert, pop, remove."""


class ReactiveSequenceBase[T, CollectionValueT, ItemValueT](
    MutableSequenceBase[T, CollectionValueT, ItemValueT],
    ViewObservableBase,
):
    """Reactive sequence — adds on_change, on_child_change, etc."""
