"""Dict set reference — unordered unique-element container."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu import AnyForm, SetForm
from nu.domains.shape import MutableSetRef, Slot

from .base import RefBase


if TYPE_CHECKING:
    from nu import Nu
    from nu.domains.shape.dsl import Shape


__all__ = [
    "SetRef",
]


class SetRef[T](MutableSetRef, RefBase[set[T]]):
    """Dict set reference — unordered unique-element container."""

    def _wrap_result(self, op: Nu) -> SetForm[T]:
        """Wrap a set-level op result as a SetForm."""
        return SetForm(op)

    def _wrap_set_result(self, operand: Nu) -> SetForm[T]:
        return SetForm(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyForm:
        return AnyForm(operand)

    def __init__(
        self,
        address: str | int | Nu,
        *,
        item_type: type[T],
        parent_ref: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address, parent_ref=parent_ref, owner_shape=owner_shape)
        self._payload["item_type"] = item_type

    @classmethod
    def slot[E](cls, item_type: type[E]) -> SetRef[E]:
        """Declare a set slot holding elements of ``item_type``."""
        return Slot(cls, item_type=item_type)  # type: ignore[return-value]

    @classmethod
    def _slot_kwargs_from_type_args(cls, args: tuple) -> dict[str, object]:
        """Derive slot kwargs from an annotation like ``SetRef[T]``."""
        (item_type,) = args
        return {"item_type": item_type}
