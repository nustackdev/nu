"""Declarative structure contracts: Shape & Slot.

A Shape defines the topology of an entity (its form).
A Slot defines a position within that form (value/nested/collection).

No behavior here — this is the declarative vocabulary only.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar


class Slot(ABC):
    """A declared position within a Shape."""

    name: str
    value_type: type[T] | None  # primitive or nested shape type
    # kind is intentionally open; higher layers can use Literals/Enums
    kind: str  # e.g., "value", "shape", "map", "list"

    def __init__(self, name: str, value_type: type[T] | None, kind: str) -> None:
        self.name = name
        self.value_type = value_type
        self.kind = kind

    @abstractmethod
    def create_ref(self, owner: Shape, parent_ref: Ref | None = None) -> Ref:
        """Produce a Ref that points at this slot, owned by a given Shape.

        Implemented by higher layers that know how refs are constructed.
        """
        ...

    def __repr__(self) -> str:  # nice for debugging
        return f"<Slot name={self.name!r} kind={self.kind} type={self.value_type}>"


class Shape(ABC):
    """Declarative form of an entity; aggregates named Slots."""

    # subclass implementations should populate this mapping
    _slots: ClassVar[dict[str, Slot]] = {}

    @classmethod
    def slots(cls) -> dict[str, Slot]:
        """Return a copy of declared slots."""
        return dict(cls._slots)

    @classmethod
    def get_slot(cls, name: str) -> Slot | None:
        return cls._slots.get(name)

    @classmethod
    def has_slot(cls, name: str) -> bool:
        return name in cls._slots
