# ruff: noqa: D102
"""PV set reference — document model + PV substrate."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from virtuals.collections import MutableSetBase

from nu import AnyI, SetI
from nu.shapes import ReactiveSetRefBase, Shape, Slot

from .base import ViewRef


if TYPE_CHECKING:
    from virtuals.loc import path

    from nu import Nu


__all__ = [
    "SetRef",
]


class SetRef[T](
    ReactiveSetRefBase[T, SetI[T], AnyI],
    ViewRef[set[T], MutableSetBase],
):
    """PV set reference — document model + PV substrate.

    Operations work lazily on PV views without loading into memory.
    """

    def result(self, op: Nu) -> SetI[T]:
        return SetI(op)

    def _wrap_set_result(self, operand: Nu) -> SetI[T]:
        return SetI(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyI:
        return AnyI(operand)

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        item_type: type[T],
        view_type: type[MutableSetBase],
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize set reference."""
        super().__init__(
            address=address, view_type=view_type, parent=parent, owner_shape=owner_shape
        )
        self.item_type = item_type

    @classmethod
    def slot(
        cls,
        item_type: type[T],
        view_type: type[MutableSetBase] | None = None,
    ) -> Self:
        """Create a slot for this set ref type.

        Args:
            item_type: Python type of items (primitives)
            view_type: View class implementing MutableSetBase protocol

        Returns:
            Slot configured to create SetRef instances
        """
        from virtuals.views import SetView

        return Slot(
            cls,
            item_type=item_type,
            view_type=view_type or SetView,
        )  # type: ignore
