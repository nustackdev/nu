# ruff: noqa: D102
"""PV shapes list reference — document model + PV substrate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from virtuals.collections import MutableSequenceBase

from nu import AnyI, IteratorI, ListI, ensure_nu
from nu.shapes import ReactiveShapesSequenceRef, Shape, Slot

from .base import ViewRef
from .shape import ShapeRef


if TYPE_CHECKING:
    from virtuals.loc import path

    from nu import Sentinel, Nu


__all__ = [
    "ShapesListRef",
]


class ShapesListRef[T: Shape](
    ReactiveShapesSequenceRef[T],
    ViewRef[
        list[dict],
        MutableSequenceBase,
    ],
):
    """PV shapes list reference — document model + PV substrate."""

    def result(self, op: Nu) -> ListI:
        return ListI(op)

    def _wrap_iterable_result(self, operand: Nu) -> IteratorI:
        return IteratorI(operand)

    def _wrap_sliceable_result(self, operand: Nu) -> ListI:
        return ListI(operand)  # slices stay materialized

    def _wrap_element_result(self, operand: Nu) -> AnyI:
        return AnyI(operand)

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        shape_type: type[T],
        view_type: type[MutableSequenceBase],
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize sequence shape reference."""
        super().__init__(
            address=address, view_type=view_type, parent=parent, owner_shape=owner_shape
        )
        self._shape_type = shape_type
        self.item_type = dict

    def _create_item_ref(self, index: int | Sentinel | Nu[int | Sentinel]) -> ShapeRef[T]:
        """Create a reference to a shape at the given index."""
        from virtuals.views import DictView

        return ShapeRef(
            address=ensure_nu(index),
            shape_type=self._shape_type,
            view_type=DictView,
            parent=self,
            owner_shape=self._owner_shape,
        )

    @classmethod
    def slot[S: Shape](
        cls,
        shape_type: type[S],
        view_type: type[MutableSequenceBase] | None = None,
    ) -> ShapesListRef[S]:
        """Create a slot for this shapes list ref type.

        Args:
            shape_type: Shape class for items
            view_type: View class implementing MutableSequenceBase protocol

        Returns:
            Slot configured to create ShapesListRef instances
        """
        from virtuals.views import ListView

        return Slot(
            cls,
            shape_type=shape_type,
            view_type=view_type or ListView,
        )  # type: ignore
