# ruff: noqa: D102
"""virtuals set reference — document model + virtuals substrate."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Self

from nu import AnyForm, SetForm
from nu.shapes import ReactiveSetRef, Shape, Slot
from nu.terms import Mode
from virtuals.collections import MutableSetBase

from .base import ViewRef


if TYPE_CHECKING:
    from nu import Nu
    from virtuals.loc import path


__all__ = [
    "SetRef",
]


class SetRef[T](
    ReactiveSetRef[T, SetForm[T], AnyForm],
    ViewRef[set[T], MutableSetBase],
):
    """virtuals set reference — document model + virtuals substrate.

    Operations work lazily on virtuals views without loading into memory.
    """

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def result(self, op: Nu) -> SetForm[T]:
        return SetForm(op)

    def _wrap_set_result(self, operand: Nu) -> SetForm[T]:
        return SetForm(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyForm:
        return AnyForm(operand)

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
