"""PV shape reference — document model + PV substrate."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from pv.collections import MutableMappingView
from pv.types import Value as StorageValue

from eb_shape import ReactiveShapeRef, Shape, Slot
from eb_shape import Ref as EveryshapeRef
from everybase.abc import AnyValue, DictValue, ListValue

from .base import ViewRef


if TYPE_CHECKING:
    from pv.loc import path

    from everybase import Term


__all__ = [
    "ShapeRef",
]


class ShapeRef[T: Shape](
    ReactiveShapeRef[T],
    ViewRef[
        dict[str, StorageValue],
        MutableMappingView,
    ],
):
    """PV shape reference — document model + PV substrate.

    Inherits attribute navigation and _create_child_ref from eb_shape ShapeRef.
    Inherits PV path resolution and view fetching from ViewRef.
    """

    # Extend passthrough with PV-specific attributes
    _PASSTHROUGH_ATTRS: ClassVar[frozenset[str]] = ReactiveShapeRef._PASSTHROUGH_ATTRS | frozenset(
        {
            "view_type",
            "_view_type",
            "result",
        }
    )

    def result(self, op: Term) -> DictValue[str, object]:
        """Wrap morphism in DictValue for shape extract/store."""
        return DictValue(op)

    def _wrap_keys_result(self, operand: Term) -> ListValue:
        return ListValue(operand)

    def _wrap_values_result(self, operand: Term) -> ListValue:
        return ListValue(operand)

    def _wrap_items_result(self, operand: Term) -> ListValue:
        return ListValue(operand)

    def _wrap_iterable_result(self, operand: Term) -> ListValue:
        return ListValue(operand)

    def _wrap_value_result(self, operand: Term) -> AnyValue:
        return AnyValue(operand)

    def _wrap_element_result(self, operand: Term) -> AnyValue:
        return AnyValue(operand)

    def __init__(
        self,
        address: path.PathAddress | Term,
        shape_type: type[T],
        view_type: type[MutableMappingView],
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize shape reference.

        Bypasses cooperative super().__init__() because the diamond MRO
        mangles positional args between eb_shape.ShapeRef (shape_type first)
        and ViewRef (address first).
        """
        EveryshapeRef.__init__(self, address, parent, owner_shape)
        self._shape_type = shape_type
        self._view_type = view_type
        self.key_type: type = str
        self.value_type: type = object

    @classmethod
    def slot(
        cls,
        shape_type: type[T],
        view_type: type[MutableMappingView] | None = None,
    ) -> T:
        """Create a slot for this shape ref type.

        Args:
            shape_type: Shape class for the nested structure
            view_type: View class implementing MutableMappingView protocol

        Returns:
            Slot configured to create ShapeRef instances
        """
        from eb_pv.views import DictView

        return Slot(
            cls,
            shape_type=shape_type,
            view_type=view_type or DictView,
        )  # type: ignore
