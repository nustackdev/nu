"""PV shape reference — document model + PV substrate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from virtuals.collections import MutableMappingBase
from virtuals.types import Value as StorageValue

from nu import (
    AnyI,
    DictItemsI,
    DictKeysI,
    DictI,
    DictValuesI,
    IteratorI,
)
from nu.shapes import ReactiveShapeRef, Shape, Slot

from .base import ViewRef


if TYPE_CHECKING:
    from virtuals.loc import path

    from nu import Nu


__all__ = [
    "ShapeRef",
]


class ShapeRef[T: Shape](
    ReactiveShapeRef[T],
    ViewRef[
        dict[str, StorageValue],
        MutableMappingBase,
    ],
):
    """PV shape reference — document model + PV substrate.

    Inherits attribute navigation and _create_child_ref from nu.shape ShapeRef.
    Inherits PV path resolution and view fetching from ViewRef.
    """

    def result(self, op: Nu) -> DictI[str, object]:
        """Wrap morphism in DictI for shape extract/store."""
        return DictI(op)

    def _wrap_keys_result(self, operand: Nu) -> DictKeysI:
        return DictKeysI(operand)

    def _wrap_values_result(self, operand: Nu) -> DictValuesI:
        return DictValuesI(operand)

    def _wrap_items_result(self, operand: Nu) -> DictItemsI:
        return DictItemsI(operand)

    def _wrap_iterable_result(self, operand: Nu) -> IteratorI:
        return IteratorI(operand)

    def _wrap_value_result(self, operand: Nu) -> AnyI:
        return AnyI(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyI:
        return AnyI(operand)

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        shape_type: type[T],
        view_type: type[MutableMappingBase],
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize shape reference."""
        super().__init__(
            address=address,
            shape_type=shape_type,
            view_type=view_type,
            parent=parent,
            owner_shape=owner_shape,
        )
        self.key_type: type = str
        self.value_type: type = object

    @classmethod
    def slot[S: Shape](
        cls,
        shape_type: type[S],
        view_type: type[MutableMappingBase] | None = None,
    ) -> S:
        """Create a slot for this shape ref type.

        Args:
            shape_type: Shape class for the nested structure
            view_type: View class implementing MutableMappingBase protocol

        Returns:
            Slot configured to create ShapeRef instances
        """
        from virtuals.views import DictView

        return Slot(
            cls,
            shape_type=shape_type,
            view_type=view_type or DictView,
        )  # type: ignore
