"""PV shape reference — document model + PV substrate."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Self

from pv.collections import MutableMappingView
from pv.types import Value as StorageValue

from everyshape import ReactiveShapeRef, Shape, Slot

from .base import ViewRef


if TYPE_CHECKING:
    from pv.loc import path

    from everyabc import Term


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

    Inherits attribute navigation and _create_child_ref from everyshape ShapeRef.
    Inherits PV path resolution and view fetching from ViewRef.
    """

    # Extend passthrough with PV-specific attributes
    _PASSTHROUGH_ATTRS: ClassVar[frozenset[str]] = ReactiveShapeRef._PASSTHROUGH_ATTRS | frozenset(
        {
            "view_type",
            "_view_type",
        }
    )

    def __init__(
        self,
        address: path.PathAddress | Term,
        shape_type: type[T],
        view_type: type[MutableMappingView],
        parent: ViewRef | None = None,
        shape: type[Shape] | None = None,
    ) -> None:
        """Initialize shape reference."""
        super().__init__(address, view_type, parent, shape)
        self._shape_type = shape_type
        self.key_type: type = str
        self.value_type: type = object

    @classmethod
    def slot(
        cls,
        shape_type: type[T],
        view_type: type[MutableMappingView] | None = None,
    ) -> Self:
        """Create a slot for this shape ref type.

        Args:
            shape_type: Shape class for the nested structure
            view_type: View class implementing MutableMappingView protocol

        Returns:
            Slot configured to create ShapeRef instances
        """
        from every_pv.views import DictView

        return Slot(
            cls,
            shape_type=shape_type,
            view_type=view_type or DictView,
        )  # type: ignore
