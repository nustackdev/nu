# ruff: noqa: D102
"""Dict set reference — unordered unique-element container backed by nested dict."""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase.abc import AnyValue, SetValue
from everyshape import MutableSetRefBase, Slot

from .base import RefBase


if TYPE_CHECKING:
    from typing import Self

    from everybase import Term
    from everyshape import Shape


__all__ = [
    "SetRef",
]


class SetRef[T](
    MutableSetRefBase[T, SetValue[T], AnyValue],
    RefBase[set[T]],
):
    """Dict set reference — unordered unique-element container backed by nested dict."""

    def result(self, op: Term) -> SetValue[T]:
        return SetValue(op)

    def _wrap_set_result(self, operand: Term) -> SetValue[T]:
        return SetValue(operand)

    def _wrap_element_result(self, operand: Term) -> AnyValue:
        return AnyValue(operand)

    def __init__(
        self,
        address: str | int | Term,
        item_type: type[T],
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize set reference."""
        super().__init__(address, parent, owner_shape)
        self.item_type = item_type

    @classmethod
    def slot(cls, item_type: type[T]) -> Self:
        """Create a slot for this set ref type.

        Args:
            item_type: Python type of items.

        Returns:
            Slot that creates SetRef instances.
        """
        return Slot(cls, item_type=item_type)  # type: ignore[return-value]
