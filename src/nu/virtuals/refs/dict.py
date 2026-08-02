"""Virtuals mapping reference: key-value container backed by a virtuals View."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu import (
    Any,
    Dict,
    DictItems,
    DictKeys,
    DictValues,
    Iterator,
)
from nu.domains.shape import ReactiveMappingRef, Slot
from nu.lang.typeinfo import value_type_for

from .base import ViewRef
from .items import ItemRef


if TYPE_CHECKING:
    from nu import Nu
    from nu.domains.shape.dsl import Shape
    from virtuals.collections import MutableMappingBase


__all__ = [
    "DictRef",
]


class DictRef[K, V](ReactiveMappingRef["ItemRef"], ViewRef[dict[K, V]]):
    """Virtuals mapping reference: key-value container backed by a virtuals View."""

    def _wrap_item_ref(self, address: object) -> ItemRef:
        """Navigate to the value at ``address`` as a substrate-backed virtuals ItemRef."""
        return ItemRef(
            address=address,
            value_type=self._payload["value_type"],
            value_value_type=self._payload["value_value_type"],
            parent_ref=self,
            owner_shape=self._owner_shape,
        )

    def _wrap_result(self, op: Nu) -> Dict[K, V]:
        """Wrap a mapping-level op result as a Dict."""
        return Dict(op)

    def _wrap_keys_result(self, operand: Nu) -> DictKeys:
        return DictKeys(operand)

    def _wrap_values_result(self, operand: Nu) -> DictValues:
        return DictValues(operand)

    def _wrap_items_result(self, operand: Nu) -> DictItems:
        return DictItems(operand)

    def _wrap_iterable_result(self, operand: Nu) -> Iterator:
        return Iterator(operand)

    def _wrap_value_result(self, operand: Nu) -> Any:
        return Any(operand)

    def _wrap_element_result(self, operand: Nu) -> Any:
        return Any(operand)

    def _wrap_mapping_result(self, operand: Nu) -> Dict[K, V]:
        return Dict(operand)

    def __init__(
        self,
        address: str | int | Nu,
        *,
        value_type: type[V],
        key_type: type[K],
        key_value_type: type,
        value_value_type: type,
        view_type: type[MutableMappingBase],
        parent_ref: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address, view_type=view_type, parent_ref=parent_ref, owner_shape=owner_shape
        )
        self._payload["value_type"] = value_type
        self._payload["key_type"] = key_type
        self._payload["key_value_type"] = key_value_type
        self._payload["value_value_type"] = value_value_type

    @classmethod
    def slot[DK, DV](
        cls,
        value_type: type[DV],
        view_type: type[MutableMappingBase] | None = None,
        key_type: type[DK] = str,  # type: ignore[assignment]
    ) -> DictRef[DK, DV]:
        """Declare a mapping slot with ``value_type`` values and ``key_type`` keys."""
        from virtuals.views import DictView

        return Slot(
            cls,
            value_type=value_type,
            key_type=key_type,
            key_value_type=value_type_for(key_type),
            value_value_type=value_type_for(value_type),
            view_type=view_type or DictView,
        )  # type: ignore[return-value]

    @classmethod
    def _slot_kwargs_from_type_args(cls, args: tuple) -> dict[str, object]:
        """Derive slot kwargs from an annotation like ``DictRef[K, V]``."""
        from virtuals.views import DictView

        key_type, value_type = args
        return {
            "value_type": value_type,
            "key_type": key_type,
            "key_value_type": value_type_for(key_type),
            "value_value_type": value_type_for(value_type),
            "view_type": DictView,
        }
