# ruff: noqa: D102
"""Sequence collection RefBases — three tiers for the document model.

SequenceRefBase         = everybase.SequenceBase + Existable + Extractable + Ref
MutableSequenceRefBase  = everybase.MutableSequenceBase + SequenceRefBase + Lengthable + Clearable + Storable
ReactiveSequenceRefBase = MutableSequenceRefBase + ViewObservable

These provide the bridge between everybase's _wrap_* hooks and everyshape's
simpler result()/element_result() abstracts. Downstream substrates only need
to implement result() and element_result().
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from everybase.collections import MutableSequenceBase, SequenceBase
from everyshape.capabilities import (
    CollectionClearableBase,
    CollectionExistableBase,
    CollectionExtractableBase,
    CollectionLengthableBase,
    CollectionStorableBase,
    ViewObservableBase,
)

from ..ref import Ref


if TYPE_CHECKING:
    from everyabc import Term


__all__ = [
    "MutableSequenceRefBase",
    "ReactiveSequenceRefBase",
    "SequenceRefBase",
]


# =============================================================================
# SEQUENCE REF — three tiers
# =============================================================================


class SequenceRefBase[T, CollectionValueT, ItemValueT](
    SequenceBase[list[T], T, CollectionValueT, ItemValueT],
    CollectionExistableBase,
    CollectionExtractableBase[CollectionValueT],
    Ref[list[T]],
):
    """Base for sequence refs — ordered containers in the document model.

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


class MutableSequenceRefBase[T, CollectionValueT, ItemValueT](
    MutableSequenceBase[list[T], T, CollectionValueT, ItemValueT],
    SequenceRefBase[T, CollectionValueT, ItemValueT],
    CollectionLengthableBase,
    CollectionClearableBase,
    CollectionStorableBase[CollectionValueT, list[T]],
):
    """Mutable sequence ref — adds append, extend, insert, pop, remove.

    Also adds length(), clear(), store() from everyshape capabilities.
    Diamond at SequenceBase resolved by C3 linearization.
    """


class ReactiveSequenceRefBase[T, CollectionValueT, ItemValueT](
    MutableSequenceRefBase[T, CollectionValueT, ItemValueT],
    ViewObservableBase,
):
    """Reactive sequence ref — adds on_change, on_child_change, etc."""
