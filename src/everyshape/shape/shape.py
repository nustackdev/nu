"""Shape system - declarative structure definitions.

## Shapes

Shapes define the topology of data structures using Slots.
The metaclass collects slot definitions and creates descriptors
for IDE-friendly access.

Example:
    class Order(Shape):
        price = ValueSlot(float)
        volume = ValueSlot(int)

    class Market(Shape):
        signal = ValueSlot(float)
        orders = MapSlot(Order)

    # Access creates refs
    Market.signal  # → ValueRef
    Market.orders["AAPL"].price  # → MapItemRef → ValueRef

## Slots

Slots are factories that create Refs. They define:
- What type of data lives at a location (value_type)
- How to access it (view_type)
- How to create refs to it (create_ref)

Slots are declarative - they describe structure, not behavior.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar


if TYPE_CHECKING:
    from .term import Ref


__all__ = [
    "Shape",
    "ShapeMeta",
    "Slot",
    "SlotDescriptor",
]


# ============================================================================
# Slot base class
# ============================================================================


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

    def __init__(self) -> None:
        """Init Slot."""
        self.name: str | None = None  # Set by metaclass

    @abstractmethod
    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> Ref:
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
        return f"<{self.__class__.__name__} name={self.name!r}>"


# ============================================================================
# Slot Descriptor
# ============================================================================


class SlotDescriptor:
    """Descriptor that creates refs when slots are accessed.

    Bridges slot definitions (declarative) to refs (runtime).

    When you access a slot on a Shape class:
        Market.signal  # SlotDescriptor.__get__() is called

    This delegates to:
        slot.create_ref(owner_shape=Market, parent_ref=None)

    Which returns the appropriate Ref instance.
    """

    def __init__(self, name: str, slot: Slot) -> None:
        """Initialize descriptor.

        Args:
            name: Field name in the Shape
            slot: Slot definition
        """
        self.name = name
        self.slot = slot

    def __get__(self, obj: Shape | None, objtype: type[Shape] | None = None) -> Ref:
        """Return ref when slot is accessed.

        Args:
            obj: Shape instance (unused - we work at class level)
            objtype: Shape class

        Returns:
            Ref created by the slot

        Raises:
            TypeError: If accessed without shape class
        """
        if objtype is None:
            raise TypeError("SlotDescriptor requires shape class")

        # Delegate to slot - it knows how to create the right ref type
        return self.slot.create_ref(
            owner_shape=objtype,
            parent_ref=None,
        )

    def __set__(self, obj: Shape, value: object) -> None:
        """Prevent setting slots - they're structure definitions."""
        raise AttributeError(
            f"Cannot set slot '{self.name}' - slots are read-only structure definitions"
        )


# ============================================================================
# Shape Metaclass
# ============================================================================


class ShapeMeta(type):
    """Metaclass that collects slot definitions into _slots dict.

    Processing steps:
    1. Collect slots from base classes (inheritance)
    2. Scan class namespace for Slot instances
    3. Store in _slots class variable
    4. Replace Slot instances with SlotDescriptors

    This happens at class definition time, not instantiation.
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
        **kwargs: object,
    ) -> type:
        """Create Shape class with slot processing.

        Args:
            name: Class name
            bases: Base classes
            namespace: Class namespace
            **kwargs: Additional metaclass arguments

        Returns:
            New Shape class with processed slots
        """
        slots: dict[str, Slot] = {}

        # 1. Collect slots from base classes (inheritance)
        for base in bases:
            if hasattr(base, "_slots"):
                slots.update(base._slots)

        # 2. Scan namespace for Slot instances
        for field_name, value in namespace.items():
            if isinstance(value, Slot):
                # Set the slot's name (it doesn't know it yet)
                value.name = field_name
                slots[field_name] = value

        # 3. Store slots in class variable
        namespace["_slots"] = slots

        # 4. Create the class
        cls = super().__new__(mcs, name, bases, namespace)

        # 5. Replace Slot instances with SlotDescriptors
        for field_name, slot in slots.items():
            setattr(cls, field_name, SlotDescriptor(field_name, slot))

        return cls


# ============================================================================
# Shape Base Class
# ============================================================================


class Shape(metaclass=ShapeMeta):
    """Base class for declarative structure definitions.

    Shapes define what exists and where it lives, using Slots.
    They are purely structural - no behavior or validation logic.

    Shapes are:
    - Declarative: Define structure, not behavior
    - Composable: Shapes can contain other Shapes
    - Type-safe: IDE autocomplete works via descriptors
    - Extensible: New slot types work automatically

    Example:
        class Profile(Shape):
            email = ValueSlot(str)
            age = ValueSlot(int)

        class User(Shape):
            name = ValueSlot(str)
            profile = ShapeSlot(Profile)
            orders = MapSlot(Order)

        # Access creates refs
        User.name  # → ValueRef
        User.profile.email  # → ShapeRef → ValueRef
        User.orders["ORDER123"]  # → MapItemRef

    Design Notes:
        - Shape classes are never instantiated
        - All access is at class level
        - Slots are replaced by descriptors at class creation
        - _slots dict is populated by metaclass
    """

    _slots: ClassVar[dict[str, Slot]] = {}
    """Mapping of field names to Slot definitions."""

    def extract(self) -> object:
        """Extracts Shape data."""
        ...

    def store(self, obj: object) -> None:
        """Stores Shape data."""
        ...
