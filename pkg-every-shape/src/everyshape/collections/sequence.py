# ruff: noqa: D102
"""Sequence collection bases — three tiers for the document model.

SequenceBase         = everybase.SequenceBase + Existable + Extractable
MutableSequenceBase  = everybase.MutableSequenceBase + SequenceBase + Lengthable + Clearable + Storable
ReactiveSequenceBase = MutableSequenceBase + ViewObservable

These provide the bridge between everybase's _wrap_* hooks and everyshape's
simpler result()/element_result() abstracts. Downstream substrates only need
to implement result() and element_result().
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from everybase.collections import MutableSequenceBase as _EB_MutableSequenceBase
from everybase.collections import SequenceBase as _EB_SequenceBase
from everyshape.capabilities import (
    CollectionClearableBase,
    CollectionExistableBase,
    CollectionExtractableBase,
    CollectionLengthableBase,
    CollectionStorableBase,
    ViewObservableBase,
)


if TYPE_CHECKING:
    from everyabc import Term


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

    Bridges everybase's _wrap_* hooks to two abstract methods:
        result(op) -> CollectionValueT       (collection-level ops)
        element_result(op) -> ItemValueT     (element-level ops)

    Substrates implement result() and element_result() to get all
    everybase sequence ops (map_, filter_, first, last, etc.) plus
    everyshape capabilities (exists, get/extract).
    """

    # -- Bridge: everybase _wrap_* → everyshape abstracts --

    def _wrap_iterable_result(self, operand: Term) -> CollectionValueT:
        return self.result(operand)

    def _wrap_sliceable_result(self, operand: Term) -> CollectionValueT:
        return self.result(operand)

    def _wrap_element_result(self, operand: Term) -> ItemValueT:
        return self.element_result(operand)

    # -- Abstract: downstream substrates implement these --

    @abstractmethod
    def element_result(self, op: Term) -> ItemValueT: ...


class MutableSequenceBase[T, CollectionValueT, ItemValueT](
    _EB_MutableSequenceBase[list[T], T, CollectionValueT, ItemValueT],
    SequenceBase[T, CollectionValueT, ItemValueT],
    CollectionLengthableBase,
    CollectionClearableBase,
    CollectionStorableBase[CollectionValueT, list[T]],
):
    """Mutable sequence — adds append, extend, insert, pop, remove.

    Also adds length(), clear(), store() from everyshape capabilities.
    Diamond at _EB_SequenceBase resolved by C3 linearization.
    """


class ReactiveSequenceBase[T, CollectionValueT, ItemValueT](
    MutableSequenceBase[T, CollectionValueT, ItemValueT],
    ViewObservableBase,
):
    """Reactive sequence — adds on_change, on_child_change, etc."""
