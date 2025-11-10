"""Slot definition - building blocks for Shapes.

Slots are factories that create Refs. They define:
- What type of data lives at a location (value_type)
- How to access it (view_type)
- How to create refs to it (create_ref)

Slots are declarative - they describe structure, not behavior.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from ..evaluation import LValue
    from .shape import Shape


__all__ = [
    "Slot",
]


class Slot(ABC):
    """Abstract base for all slot types.

    Slots are structure definitions that create refs when accessed.
    They act as factories - constructing refs with appropriate types.

    All slots must implement:
        - create_ref(): Factory method that produces a Ref

    Attributes:
        name: Field name (set by Shape metaclass)
        value_type: Type of data at this location
        view_type: View class for accessing this location
    """

    def __init__(self, value_type: type, view_type: type) -> None:
        """Initialize slot.

        Args:
            value_type: Python type of the value (int, str, Order, etc.)
            view_type: View class for access
        """
        self.name: str | None = None  # Set by metaclass
        self.value_type = value_type
        self.view_type = view_type

    @abstractmethod
    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: LValue | None = None,
    ) -> LValue:
        """Create ref for this slot.

        This is the factory method - each slot type creates its
        corresponding ref type.

        Args:
            owner_shape: Shape class this slot belongs to
            parent_ref: Parent ref (for nested access)

        Returns:
            Appropriate Ref instance
        """
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r} type={self.value_type}>"
