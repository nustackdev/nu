"""Shape DSL: Shape, Slot, ShapeMeta, SlotDescriptor.

Metaclass-driven DSL for declaring hierarchical document structures.
Slot is the factory; ShapeMeta collects slots at class-definition time;
SlotDescriptor exposes them as Refs on class access.

Example::

    class Order(Shape):
        price = FloatRef.slot()
        qty   = IntRef.slot()

    Order.price   # -> Ref rooted at Order
"""

from __future__ import annotations

from abc import ABCMeta
from typing import TYPE_CHECKING, ClassVar, Generic, TypeVar


if TYPE_CHECKING:
    from nu.domains.shape.refs.base import _StructuredRef

__all__ = [
    "Shape",
    "ShapeMeta",
    "Slot",
    "SlotDescriptor",
]

_RefT = TypeVar("_RefT")


class Slot(Generic[_RefT]):  # noqa: UP046
    """Factory carrying a Ref class and kwargs; create_ref produces the Ref."""

    def __init__(self, ref_cls: type[_RefT], **kwargs: object) -> None:
        self.name: str | None = None
        self.ref_cls = ref_cls
        self.kwargs = kwargs

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: _StructuredRef | None = None,
    ) -> _RefT:
        """Instantiate the Ref, wiring owner_shape and parent_ref."""
        return self.ref_cls(  # type: ignore[call-arg]
            self.name,
            owner_shape=owner_shape,
            parent_ref=parent_ref,
            **self.kwargs,
        )

    def __repr__(self) -> str:
        return f"<Slot name={self.name!r} ref_cls={self.ref_cls.__name__}>"


class SlotDescriptor:
    """Descriptor that returns a Ref when a slot name is accessed on a Shape class."""

    def __init__(self, name: str, slot: Slot) -> None:
        self.name = name
        self.slot = slot

    def __get__(self, obj: object, objtype: type[Shape] | None = None) -> _StructuredRef:
        """Return a Ref rooted at objtype for this slot."""
        if objtype is None:
            raise TypeError("SlotDescriptor requires a Shape class")
        return self.slot.create_ref(owner_shape=objtype, parent_ref=None)  # type: ignore[return-value]

    def __set__(self, obj: object, value: object) -> None:
        """Slots are read-only structure definitions."""
        raise AttributeError(
            f"Cannot set slot '{self.name}' — slots are read-only structure definitions"
        )


class ShapeMeta(ABCMeta):
    """Metaclass that collects Slot definitions and replaces them with SlotDescriptors."""

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
        **kwargs: object,
    ) -> type:
        """Build the Shape class, collecting and replacing Slot entries."""
        slots: dict[str, Slot] = {}
        for base in bases:
            if hasattr(base, "_slots"):
                slots.update(base._slots)
        for field_name, value in list(namespace.items()):
            if isinstance(value, Slot):
                value.name = field_name
                slots[field_name] = value
        namespace["_slots"] = slots
        cls = super().__new__(mcs, name, bases, namespace)
        for field_name, slot in slots.items():
            setattr(cls, field_name, SlotDescriptor(field_name, slot))
        return cls


class Shape(metaclass=ShapeMeta):
    """Declarative structure definition using Slots. Never instantiated.

    Slots are replaced by SlotDescriptors at class-definition time.
    All access is at class level; Shape instances are never created.

    Example::

        class Profile(Shape):
            email = StrRef.slot()
            age   = IntRef.slot()

        class User(Shape):
            name    = StrRef.slot()
            profile = ShapeRef.slot(shape_type=Profile)

        User.name            # -> Ref
        User.profile.email   # -> Ref (nested via ShapeRef.__getattr__)
    """

    _slots: ClassVar[dict[str, Slot]] = {}
