"""Declarative shape structure definitions.

Shapes use Slot/SlotDescriptor/ShapeMeta to define hierarchical
document structures. Slots are factories that create refs.

Example::

    class Order(Shape):
        price = FloatRef.slot()
        volume = IntRef.slot()

    Order.price   # -> ref
    Order.volume  # -> ref
"""

from __future__ import annotations

from abc import ABCMeta
from typing import TYPE_CHECKING, ClassVar

from nu import Model

from .slot import Slot


if TYPE_CHECKING:
    from nu import Context, Ref, Sentinel
    from nu.abc import NoneValue


__all__ = [
    "Shape",
    "ShapeMeta",
    "SlotDescriptor",
]


class SlotDescriptor:
    """Descriptor that creates refs when slots are accessed on a shape.

    Bridges slot definitions (declarative) to refs (runtime).

    When you access a slot on a shape class::

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

    def __get__(self, obj: Shape | None, objtype: type[Shape] | None = None) -> Ref:
        """Return ref when slot is accessed.

        Args:
            obj: Shape instance (unused -- class-level access).
            objtype: Shape class.

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

    def __set__(self, obj: Shape, value: object) -> None:
        """Prevent setting slots -- they're structure definitions."""
        raise AttributeError(
            f"Cannot set slot '{self.name}' - slots are read-only structure definitions"
        )


class ShapeMeta(ABCMeta):
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
        """Create shape class with slot processing."""
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


class Shape(Model, metaclass=ShapeMeta):
    """Declarative structure definitions using Slots.

    Shape classes are never instantiated. All access is at class level.
    Slots are replaced by descriptors at class creation.

    Example::

        class Profile(Shape):
            email = StrRef.slot()
            age = IntRef.slot()

        class User(Shape):
            name = StrRef.slot()
            profile = ShapeRef.slot(Profile)

        User.name            # -> ref
        User.profile.email   # -> ref (nested)
    """

    _slots: ClassVar[dict[str, Slot]] = {}
    """Mapping of field names to Slot definitions."""

    # Type stubs for Ref methods. At runtime, shape refs (ShapeRef[T])
    # provide these — but since __getitem__ returns T (type lie for slot
    # navigation), Shape needs the signatures so Pyright can resolve
    # Market.orders[0].execute(ctx) etc.
    if TYPE_CHECKING:

        async def execute(self, ctx: Context) -> object | Sentinel:  # noqa: D102
            ...

        def store(  # noqa: D102
            self, value: object
        ) -> NoneValue: ...

        def erase(self) -> NoneValue:  # noqa: D102
            ...
