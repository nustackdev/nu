"""Dict shape reference — structured container backed by nested dict."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from eb_shape import MutableShapeRef, Slot

from .base import RefBase


if TYPE_CHECKING:
    from typing import Self

    from eb_shape import Shape
    from everybase import Term


__all__ = [
    "ShapeRef",
]


class ShapeRef[T: Shape](
    MutableShapeRef[T],
    RefBase[dict[str, object]],
):
    """Dict shape reference — structured container backed by nested dict."""

    _PASSTHROUGH_ATTRS: ClassVar[frozenset[str]] = MutableShapeRef._PASSTHROUGH_ATTRS

    def __init__(
        self,
        address: str | int | Term,
        shape_type: type[T],
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize shape reference."""
        super().__init__(address, parent, owner_shape)
        self._shape_type = shape_type
        self.key_type: type = str
        self.value_type: type = object

    @classmethod
    def slot(cls, shape_type: type[T]) -> Self:
        """Create a slot for this shape ref type.

        Args:
            shape_type: Shape class for the nested structure.

        Returns:
            Slot that creates ShapeRef instances.
        """
        return Slot(cls, shape_type=shape_type)  # type: ignore[return-value]
