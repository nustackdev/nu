"""Slot -- abstract field definition that creates Refs."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from everyabc import Ref

    from .shape import Shape


__all__ = [
    "Slot",
]


class Slot(ABC):
    """Abstract base for all slot types.

    Slots are structure definitions that create refs when accessed.
    They act as factories -- constructing refs with appropriate types.

    Concrete implementations live in substrate packages:
    - every_pv: PV storage slots (ItemSlot, DictSlot, etc.)

    All slots must implement:
        create_ref(): Factory method that produces a Ref.
    """

    def __init__(self) -> None:
        """Initialize slot. Name is set by the shape metaclass."""
        self.name: str | None = None

    @abstractmethod
    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> Ref:
        """Create ref for this slot.

        Args:
            owner_shape: Shape class this slot belongs to.
            parent_ref: Parent ref (for nested access).

        Returns:
            Appropriate Ref instance.
        """
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"
