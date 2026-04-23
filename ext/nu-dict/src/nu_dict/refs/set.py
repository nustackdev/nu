# ruff: noqa: D102
"""Dict set reference — unordered unique-element container."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from nu import AnyI, SetI
from nu.shapes import MutableSetRef, Slot
from nu.terms import Mode

from .base import RefBase


if TYPE_CHECKING:
    from nu import Nu


__all__ = [
    "SetRef",
]


class SetRef[T](
    MutableSetRef[T, SetI[T], AnyI],
    RefBase[set[T]],
):
    """Dict set reference — unordered unique-element container."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def result(self, op: Nu) -> SetI[T]:
        return SetI(op)

    def _wrap_set_result(self, operand: Nu) -> SetI[T]:
        return SetI(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyI:
        return AnyI(operand)

    def __init__(
        self,
        *,
        item_type: type[T],
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self.item_type = item_type

    @classmethod
    def slot[E](cls, item_type: type[E]) -> SetRef[E]:
        return Slot(cls, item_type=item_type)  # type: ignore[return-value]
