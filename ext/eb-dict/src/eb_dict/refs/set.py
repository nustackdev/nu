# ruff: noqa: D102
"""Dict set reference — unordered unique-element container."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from everybase.abc import AnyValue, SetValue
from everybase.shape import MutableSetRefBase, Slot

from .base import RefBase


if TYPE_CHECKING:
    from everybase import Term


__all__ = [
    "SetRef",
]


class SetRef[T](
    MutableSetRefBase[T, SetValue[T], AnyValue],
    RefBase[set[T]],
):
    """Dict set reference — unordered unique-element container."""

    def result(self, op: Term) -> SetValue[T]:
        return SetValue(op)

    def _wrap_set_result(self, operand: Term) -> SetValue[T]:
        return SetValue(operand)

    def _wrap_element_result(self, operand: Term) -> AnyValue:
        return AnyValue(operand)

    def __init__(
        self,
        *,
        item_type: type[T],
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self.item_type = item_type

    @classmethod
    def slot(cls, item_type: type[T]) -> Self:
        return Slot(cls, item_type=item_type)  # type: ignore[return-value]
