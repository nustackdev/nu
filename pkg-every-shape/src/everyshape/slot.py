"""Slot -- field definition that creates Refs.

Slot is the universal implementation that creates any Ref type.
Used internally by Ref.slot() — users call Ref.slot(), not Slot() directly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .refs.base import Ref
    from .shape import Shape


__all__ = [
    "Slot",
]


class Slot[RefT: Ref]:
    """Universal slot that creates any Ref type.

    Used internally by Ref.slot() implementations.

    Example:
        class IntRef(PrimitiveRef[int], IntType):
            @classmethod
            def slot(cls) -> Self:
                return Slot(cls)

        class User(Shape):
            age = IntRef.slot()  # Returns Slot(IntRef)
    """

    def __init__(self, ref_cls: type[RefT], **kwargs: object) -> None:
        """Initialize slot.

        Args:
            ref_cls: The Ref class this slot will create
            **kwargs: Additional arguments passed to ref constructor
        """
        self.name: str | None = None
        self.ref_cls = ref_cls
        self.kwargs = kwargs

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> RefT:
        """Create ref by instantiating the stored ref class."""
        return self.ref_cls(
            address=self.name,
            parent=parent_ref,
            owner_shape=owner_shape,
            **self.kwargs,
        )

    def __repr__(self) -> str:
        return f"<Slot name={self.name!r} ref_cls={self.ref_cls.__name__}>"
