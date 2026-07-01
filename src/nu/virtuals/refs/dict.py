"""Virtuals mapping reference — key-value container backed by a virtuals View."""

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
from nu.domains.shape import ReactiveMappingRef, Slot

from ._typemap import value_type_for
from .base import ViewRef


if TYPE_CHECKING:
    from nu import Nu
    from nu.domains.shape.dsl import Shape
    from virtuals.collections import MutableMappingBase


__all__ = [
    "DictRef",
]


class DictRef[K, V](ReactiveMappingRef, ViewRef[dict[K, V]]):
    """Virtuals mapping reference — key-value container backed by a virtuals View."""

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
        view_type: type[MutableMappingBase],
        parent_ref: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address, view_type=view_type, parent_ref=parent_ref, owner_shape=owner_shape
        )
        self.value_type = value_type
        self.key_type = key_type
        self.key_value_type = key_value_type
        self.value_value_type = value_value_type

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
