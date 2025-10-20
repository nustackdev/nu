"""Shape system - declarative structure definitions.

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
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from ..core.term import LValue


if TYPE_CHECKING:
    from .slots import Slot


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

    def __get__(self, obj: Shape | None, objtype: type[Shape] | None = None) -> LValue:
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

    def __set__(self, obj: Shape, value: Any) -> None:
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
    2. Collect slots from current class annotations
    3. Store in _slots class variable
    4. Replace Slot instances with SlotDescriptors

    This happens at class definition time, not instantiation.
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
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

        # 2. Collect slots from current class annotations
        annotations = namespace.get("__annotations__", {})
        for field_name in annotations:
            value = namespace.get(field_name)

            # Import here to avoid circular dependency
            from .slots import Slot

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

    @classmethod
    def slots(cls) -> dict[str, Slot]:
        """Return copy of all slot definitions.

        Returns:
            Dictionary mapping field names to Slot instances
        """
        return dict(cls._slots)

    @classmethod
    def get_slot(cls, name: str) -> Slot | None:
        """Get slot definition by name.

        Args:
            name: Field name

        Returns:
            Slot instance, or None if not found
        """
        return cls._slots.get(name)

    @classmethod
    def has_slot(cls, name: str) -> bool:
        """Check if shape has a slot with given name.

        Args:
            name: Field name

        Returns:
            True if slot exists
        """
        return name in cls._slots

    @classmethod
    def field_names(cls) -> list[str]:
        """Return list of all field names in this shape.

        Returns:
            List of field name strings
        """
        return list(cls._slots.keys())


__all__ = [
    "Shape",
    "ShapeMeta",
    "SlotDescriptor",
]
