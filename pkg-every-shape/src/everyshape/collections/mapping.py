# ruff: noqa: D102
"""Mapping collection bases — three tiers for the document model.

MappingBase         = everybase.MappingBase + Existable + Extractable
MutableMappingBase  = everybase.MutableMappingBase + MappingBase + Lengthable + Clearable + Storable
ReactiveMappingBase = MutableMappingBase + ViewObservable

These provide the bridge between everybase's _wrap_* hooks and everyshape's
simpler result()/element_result()/iterable_result() abstracts.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

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


if TYPE_CHECKING:
    from everyabc import Term


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

    Bridges everybase's _wrap_* hooks to three abstract methods:
        result(op) -> CollectionValueT       (extract/store)
        element_result(op) -> ValueValueT    (single-value ops: get_, set_, delete)
        iterable_result(op) -> object        (keys_, values_, items_, map_, filter_)

    Substrates implement these three to get all everybase mapping ops
    plus everyshape capabilities (exists, get/extract).
    """

    # -- Bridge: everybase _wrap_* → everyshape abstracts --

    def _wrap_keys_result(self, operand: Term) -> object:
        return self.iterable_result(operand)

    def _wrap_values_result(self, operand: Term) -> object:
        return self.iterable_result(operand)

    def _wrap_items_result(self, operand: Term) -> object:
        return self.iterable_result(operand)

    def _wrap_iterable_result(self, operand: Term) -> object:
        return self.iterable_result(operand)

    def _wrap_value_result(self, operand: Term) -> ValueValueT:
        return self.element_result(operand)

    def _wrap_element_result(self, operand: Term) -> ValueValueT:
        return self.element_result(operand)

    # -- Abstract: downstream substrates implement these --

    @abstractmethod
    def element_result(self, op: Term) -> ValueValueT: ...

    @abstractmethod
    def iterable_result(self, op: Term) -> object: ...


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
