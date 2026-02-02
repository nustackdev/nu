"""Slot -- field definition that creates Refs.

Slot is the universal implementation that creates any Ref type.
Used internally by Ref.slot() — users call Ref.slot(), not Slot() directly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .shape import Shape
    from .shape_ref import Ref


__all__ = [
    "Slot",
]


class _SlotBase(ABC):
    """Abstract base for slots (internal, for isinstance checks)."""

    def __init__(self) -> None:
        self.name: str | None = None

    @abstractmethod
    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> Ref:
        """Create ref for this slot."""
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"


class Slot[RefT: Ref](_SlotBase):
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
        super().__init__()
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
            shape=owner_shape,
            **self.kwargs,
        )

    def __repr__(self) -> str:
        return f"<Slot name={self.name!r} ref_cls={self.ref_cls.__name__}>"
