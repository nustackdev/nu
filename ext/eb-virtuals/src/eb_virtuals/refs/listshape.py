# ruff: noqa: D102
"""PV shapes list reference — document model + PV substrate."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from virtuals.collections import MutableSequenceView

from everybase.abc import AnyValue, ListValue, ensure_term
from everybase.shape import ReactiveShapesSequenceRefBase, Shape, Slot

from .base import ViewRef
from .shape import ShapeRef


if TYPE_CHECKING:
    from virtuals.loc import path

    from everybase import Sentinel, Term


__all__ = [
    "ShapesListRef",
]


class ShapesListRef[T: Shape](
    ReactiveShapesSequenceRefBase[T],
    ViewRef[
        list[dict],
        MutableSequenceView,
    ],
):
    """PV shapes list reference — document model + PV substrate."""

    def result(self, op: Term) -> ListValue:
        return ListValue(op)

    def _wrap_iterable_result(self, operand: Term) -> ListValue:
        return ListValue(operand)

    def _wrap_sliceable_result(self, operand: Term) -> ListValue:
        return ListValue(operand)

    def _wrap_element_result(self, operand: Term) -> AnyValue:
        return AnyValue(operand)

    def __init__(
        self,
        *,
        address: path.PathAddress | Term,
        shape_type: type[T],
        view_type: type[MutableSequenceView],
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize sequence shape reference."""
        super().__init__(
            address=address, view_type=view_type, parent=parent, owner_shape=owner_shape
        )
        self._shape_type = shape_type
        self.item_type = dict

    def _create_item_ref(self, index: int | Sentinel | Term[int | Sentinel]) -> ShapeRef[T]:
        """Create a reference to a shape at the given index."""
        from virtuals.views import DictView

        return ShapeRef(
            address=ensure_term(index),
            shape_type=self._shape_type,
            view_type=DictView,
            parent=self,
            owner_shape=self._owner_shape,
        )

    @classmethod
    def slot(
        cls,
        shape_type: type[T],
        view_type: type[MutableSequenceView] | None = None,
    ) -> Self:
        """Create a slot for this shapes list ref type.

        Args:
            shape_type: Shape class for items
            view_type: View class implementing MutableSequenceView protocol

        Returns:
            Slot configured to create ShapesListRef instances
        """
        from virtuals.views import ListView

        return Slot(
            cls,
            shape_type=shape_type,
            view_type=view_type or ListView,
        )  # type: ignore
