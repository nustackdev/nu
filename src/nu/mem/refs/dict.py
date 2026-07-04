"""Dict mapping reference — key-value container backed by nested dict."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu import (
    AnyForm,
    DictForm,
    DictItemsForm,
    DictKeysForm,
    DictValuesForm,
    IteratorForm,
)
from nu.domains.shape import MutableMappingRef, Slot

from ._typemap import value_type_for
from .base import RefBase
from .items import ItemRef


if TYPE_CHECKING:
    from nu import Nu
    from nu.domains.shape.dsl import Shape


__all__ = [
    "DictRef",
]


class DictRef[K, V](MutableMappingRef["ItemRef"], RefBase[dict[K, V]]):
    """Dict mapping reference — key-value container backed by nested dict."""

    def _wrap_item_ref(self, address: object) -> ItemRef:
        """Navigate to the value at ``address`` as a substrate-backed mem ItemRef."""
        return ItemRef(
            address,
            value_type=self.payload["value_type"],
            value_value_type=self.payload["value_value_type"],
            parent_ref=self,
            owner_shape=self._owner_shape,
        )

    def result(self, op: Nu) -> DictForm[K, V]:
        """Wrap a mapping-level op result as a DictForm."""
        return DictForm(op)

    def _wrap_keys_result(self, operand: Nu) -> DictKeysForm:
        return DictKeysForm(operand)

    def _wrap_values_result(self, operand: Nu) -> DictValuesForm:
        return DictValuesForm(operand)

    def _wrap_items_result(self, operand: Nu) -> DictItemsForm:
        return DictItemsForm(operand)

    def _wrap_iterable_result(self, operand: Nu) -> IteratorForm:
        return IteratorForm(operand)

    def _wrap_value_result(self, operand: Nu) -> AnyForm:
        return AnyForm(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyForm:
        return AnyForm(operand)

    def _wrap_mapping_result(self, operand: Nu) -> DictForm[K, V]:
        return DictForm(operand)

    def __init__(
        self,
        address: str | int | Nu,
        *,
        value_type: type[V],
        key_type: type[K],
        key_value_type: type,
        value_value_type: type,
        parent_ref: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address, parent_ref=parent_ref, owner_shape=owner_shape)
        self.payload["value_type"] = value_type
        self.payload["key_type"] = key_type
        self.payload["key_value_type"] = key_value_type
        self.payload["value_value_type"] = value_value_type

    @classmethod
    def slot[DK, DV](cls, value_type: type[DV], key_type: type[DK] = str) -> DictRef[DK, DV]:  # type: ignore[assignment]
        """Declare a mapping slot with ``value_type`` values and ``key_type`` keys."""
        return Slot(
            cls,
            value_type=value_type,
            key_type=key_type,
            key_value_type=value_type_for(key_type),
            value_value_type=value_type_for(value_type),
        )  # type: ignore[return-value]
