"""Virtuals set reference: unordered unique-element container backed by a View."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu import Any, Set
from nu.domains.shape import ReactiveSetRef, Slot

from .base import ViewRef


if TYPE_CHECKING:
    from nu import Nu
    from nu.domains.shape.dsl import Shape
    from virtuals.collections import MutableSetBase


__all__ = [
    "SetRef",
]


class SetRef[T](ReactiveSetRef, ViewRef[set[T]]):
    """Virtuals set reference: unordered unique-element container backed by a View."""

    def _wrap_result(self, op: Nu) -> Set[T]:
        """Wrap a set-level op result as a Set."""
        return Set(op)

    def _wrap_set_result(self, operand: Nu) -> Set[T]:
        return Set(operand)

    def _wrap_element_result(self, operand: Nu) -> Any:
        return Any(operand)

    def __init__(
        self,
        address: str | int | Nu,
        *,
        item_type: type[T],
        view_type: type[MutableSetBase],
        parent_ref: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address, view_type=view_type, parent_ref=parent_ref, owner_shape=owner_shape
        )
        self._payload["item_type"] = item_type

    @classmethod
    def slot[E](
        cls, item_type: type[E], view_type: type[MutableSetBase] | None = None
    ) -> SetRef[E]:
        """Declare a set slot holding elements of ``item_type``."""
        from virtuals.views import SetView

        return Slot(cls, item_type=item_type, view_type=view_type or SetView)  # type: ignore[return-value]

    @classmethod
    def _slot_kwargs_from_type_args(cls, args: tuple) -> dict[str, object]:
        """Derive slot kwargs from an annotation like ``SetRef[T]``."""
        from virtuals.views import SetView

        (item_type,) = args
        return {"item_type": item_type, "view_type": SetView}
