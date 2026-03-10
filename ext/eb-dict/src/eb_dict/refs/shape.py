# ruff: noqa: D102
"""Dict shape reference — structured container backed by nested dict."""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase.abc import (
    AnyValue,
    DictItemsValue,
    DictKeysValue,
    DictValue,
    DictValuesValue,
    IteratorValue,
)
from everybase.shape import MutableShapeRef, Slot

from .base import RefBase


if TYPE_CHECKING:
    from everybase import Term
    from everybase.shape import Shape


__all__ = [
    "ShapeRef",
]


class ShapeRef[T: Shape](
    MutableShapeRef[T],
    RefBase[dict[str, object]],
):
    """Dict shape reference — structured container backed by nested dict."""

    def result(self, op: Term) -> DictValue[str, object]:
        return DictValue(op)

    def _wrap_keys_result(self, operand: Term) -> DictKeysValue:
        return DictKeysValue(operand)

    def _wrap_values_result(self, operand: Term) -> DictValuesValue:
        return DictValuesValue(operand)

    def _wrap_items_result(self, operand: Term) -> DictItemsValue:
        return DictItemsValue(operand)

    def _wrap_iterable_result(self, operand: Term) -> IteratorValue:
        return IteratorValue(operand)

    def _wrap_value_result(self, operand: Term) -> AnyValue:
        return AnyValue(operand)

    def _wrap_element_result(self, operand: Term) -> AnyValue:
        return AnyValue(operand)

    def __init__(
        self,
        *,
        address: str | int | Term,
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
