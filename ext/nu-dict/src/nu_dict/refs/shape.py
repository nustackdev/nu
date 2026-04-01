# ruff: noqa: D102
"""Dict shape reference — structured container backed by nested dict."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu import (
    AnyValue,
    DictItemsValue,
    DictKeysValue,
    DictValue,
    DictValuesValue,
    IteratorValue,
)
from nu.shapes import MutableShapeRef, Slot

from .base import RefBase


if TYPE_CHECKING:
    from nu import Nu
    from nu.shapes import Shape


__all__ = [
    "ShapeRef",
]


class ShapeRef[T: Shape](
    MutableShapeRef[T],
    RefBase[dict[str, object]],
):
    """Dict shape reference — structured container backed by nested dict."""

    def result(self, op: Nu) -> DictValue[str, object]:
        return DictValue(op)

    def _wrap_keys_result(self, operand: Nu) -> DictKeysValue:
        return DictKeysValue(operand)

    def _wrap_values_result(self, operand: Nu) -> DictValuesValue:
        return DictValuesValue(operand)

    def _wrap_items_result(self, operand: Nu) -> DictItemsValue:
        return DictItemsValue(operand)

    def _wrap_iterable_result(self, operand: Nu) -> IteratorValue:
        return IteratorValue(operand)

    def _wrap_value_result(self, operand: Nu) -> AnyValue:
        return AnyValue(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyValue:
        return AnyValue(operand)

    def __init__(
        self,
        *,
        address: str | int | Nu,
        shape_type: type[T],
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            shape_type=shape_type,
            parent=parent,
            owner_shape=owner_shape,
        )
        self.key_type: type = str
        self.value_type: type = object

    @classmethod
    def slot[S: Shape](cls, shape_type: type[S]) -> S:
        return Slot(cls, shape_type=shape_type)  # type: ignore[return-value]
