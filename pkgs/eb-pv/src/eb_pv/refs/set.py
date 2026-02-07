# ruff: noqa: D102
"""PV set reference — document model + PV substrate."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from pv.collections import MutableSetView

from eb_shape import ReactiveSetRefBase, Shape, Slot
from everybase.abc import AnyValue, SetValue

from .base import ViewRef


if TYPE_CHECKING:
    from pv.loc import path

    from everybase import Term


__all__ = [
    "SetRef",
]


class SetRef[T](
    ReactiveSetRefBase[T, SetValue[T], AnyValue],
    ViewRef[set[T], MutableSetView],
):
    """PV set reference — document model + PV substrate.

    Operations work lazily on PV views without loading into memory.
    """

    def result(self, op: Term) -> SetValue[T]:
        return SetValue(op)

    def _wrap_set_result(self, operand: Term) -> SetValue[T]:
        return SetValue(operand)

    def _wrap_element_result(self, operand: Term) -> AnyValue:
        return AnyValue(operand)

    def __init__(
        self,
        address: path.PathAddress | Term,
        item_type: type[T],
        view_type: type[MutableSetView],
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize set reference."""
        super().__init__(address, view_type, parent, owner_shape)
        self.item_type = item_type

    @classmethod
    def slot(
        cls,
        item_type: type[T],
        view_type: type[MutableSetView] | None = None,
    ) -> Self:
        """Create a slot for this set ref type.

        Args:
            item_type: Python type of items (primitives)
            view_type: View class implementing MutableSetView protocol

        Returns:
            Slot configured to create SetRef instances
        """
        from eb_pv.views import SetView

        return Slot(
            cls,
            item_type=item_type,
            view_type=view_type or SetView,
        )  # type: ignore
