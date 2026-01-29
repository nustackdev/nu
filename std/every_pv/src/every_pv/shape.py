"""PVShape -- declarative PV storage structure definitions.

PVShape uses Slot/SlotDescriptor/PVShapeMeta to define how data
maps to PV storage views. Slots are factories that create PV refs.

Example::

    class Order(PVShape):
        price = ItemSlot(float, FloatRef)
        volume = ItemSlot(int, IntRef)

    Order.price   # → PVItemRef
    Order.volume  # → PVItemRef
"""

from __future__ import annotations

from abc import ABCMeta
from typing import TYPE_CHECKING, ClassVar

from everyabc import Shape, Slot


if TYPE_CHECKING:
    from everyabc import Ref


__all__ = [
    "PVShape",
    "PVShapeMeta",
    "SlotDescriptor",
]


class SlotDescriptor:
    """Descriptor that creates refs when slots are accessed on a PVShape.

    Bridges slot definitions (declarative) to refs (runtime).

    When you access a slot on a PVShape class::

        Market.signal  # SlotDescriptor.__get__() is called

    This delegates to::

        slot.create_ref(owner_shape=Market, parent_ref=None)
    """

    def __init__(self, name: str, slot: Slot) -> None:
        """Initialize descriptor.

        Args:
            name: Field name in the Shape.
            slot: Slot definition.
        """
        self.name = name
        self.slot = slot

    def __get__(self, obj: PVShape | None, objtype: type[PVShape] | None = None) -> Ref:
        """Return ref when slot is accessed.

        Args:
            obj: PVShape instance (unused -- class-level access).
            objtype: PVShape class.

        Returns:
            Ref created by the slot.

        Raises:
            TypeError: If accessed without shape class.
        """
        if objtype is None:
            raise TypeError("SlotDescriptor requires shape class")

        return self.slot.create_ref(
            owner_shape=objtype,
            parent_ref=None,
        )

    def __set__(self, obj: PVShape, value: object) -> None:
        """Prevent setting slots -- they're structure definitions."""
        raise AttributeError(
            f"Cannot set slot '{self.name}' - slots are read-only structure definitions"
        )


class PVShapeMeta(ABCMeta):
    """Metaclass that collects slot definitions into _slots dict.

    Processing steps:
    1. Collect slots from base classes (inheritance).
    2. Scan class namespace for Slot instances.
    3. Store in _slots class variable.
    4. Replace Slot instances with SlotDescriptors.

    This happens at class definition time, not instantiation.
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
        **kwargs: object,
    ) -> type:
        """Create PVShape class with slot processing."""
        slots: dict[str, Slot] = {}

        # 1. Collect slots from base classes (inheritance)
        for base in bases:
            if hasattr(base, "_slots"):
                slots.update(base._slots)

        # 2. Scan namespace for Slot instances
        for field_name, value in namespace.items():
            if isinstance(value, Slot):
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


class PVShape(Shape, metaclass=PVShapeMeta):
    """Declarative PV structure definitions using Slots.

    PVShape classes are never instantiated. All access is at class level.
    Slots are replaced by descriptors at class creation.

    Example::

        class Profile(PVShape):
            email = StrSlot()
            age = IntSlot()

        class User(PVShape):
            name = StrSlot()
            profile = ShapeSlot(Profile)

        User.name            # → PVItemRef
        User.profile.email   # → PVItemRef (nested)
    """

    _slots: ClassVar[dict[str, Slot]] = {}
    """Mapping of field names to Slot definitions."""
