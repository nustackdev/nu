"""virtuals shape reference — document model + virtuals substrate."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from nu import (
    AnyForm,
    DictForm,
    DictItemsForm,
    DictKeysForm,
    DictValuesForm,
    IteratorForm,
)
from nu.shapes import ReactiveShapeRef, Shape, Slot
from nu.terms import Mode
from virtuals.collections import MutableMappingBase
from virtuals.types import Value as StorageValue

from .base import ViewRef


if TYPE_CHECKING:
    from nu import Nu
    from virtuals.loc import path


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
    """virtuals shape reference — document model + virtuals substrate.

    Inherits attribute navigation and _create_child_ref from nu.shape ShapeRef.
    Inherits virtuals path resolution and view fetching from ViewRef.
    """

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def result(self, op: Nu) -> DictForm[str, object]:
        """Wrap op in DictForm for shape extract/store."""
        return DictForm(op)

    def _wrap_keys_result(self, operand: Nu) -> DictKeysForm:
        return DictKeysForm(operand)

    def _wrap_values_result(self, operand: Nu) -> DictValuesForm:
        return DictValuesForm(operand)

    def _wrap_items_result(self, operand: Nu) -> DictItemsForm:
        return DictItemsForm(operand)

    def _wrap_iterable_result(self, operand: Nu) -> IteratorForm:
        return IteratorForm(operand)

    def _wrap_value_result(self, operand: Nu) -> AnyForm:
        return AnyForm(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyForm:
        return AnyForm(operand)

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
