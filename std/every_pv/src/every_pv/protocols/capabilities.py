"""PV capability protocols.

Runtime-checkable protocols for PV ref capabilities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable


if TYPE_CHECKING:
    from every import Sentinel, Term
    from everybase import BoolRef, IntRef, NoneRef


__all__ = [
    "PVClearable",
    "PVDeletable",
    "PVExistable",
    "PVExtractable",
    "PVGettable",
    "PVLengthable",
    "PVSettable",
    "PVStorable",
]


@runtime_checkable
class PVExistable(Protocol):
    """Protocol for refs that can check existence."""

    def exists(self) -> BoolRef:
        """Check if location exists."""
        ...

    def missing(self) -> BoolRef:
        """Check if location is missing."""
        ...


@runtime_checkable
class PVGettable[T](Protocol):
    """Protocol for refs that can get primitive values."""

    def get(self) -> object:
        """Get the value at this location."""
        ...


@runtime_checkable
class PVSettable[T](Protocol):
    """Protocol for refs that can set primitive values."""

    def set(self, value: T | Sentinel | Term[T | Sentinel]) -> object:
        """Set the value at this location."""
        ...


@runtime_checkable
class PVExtractable[T](Protocol):
    """Protocol for refs that can extract container contents."""

    def get(self) -> object:
        """Extract entire container structure."""
        ...


@runtime_checkable
class PVStorable[T](Protocol):
    """Protocol for refs that can store container contents."""

    def store(self, value: T | Sentinel | Term[T | Sentinel]) -> object:
        """Store entire container structure."""
        ...


@runtime_checkable
class PVDeletable(Protocol):
    """Protocol for refs that can delete values."""

    def remove(self) -> NoneRef:
        """Delete the value at this location."""
        ...


@runtime_checkable
class PVClearable(Protocol):
    """Protocol for refs that can clear all items."""

    def clear(self) -> NoneRef:
        """Clear all items from container."""
        ...


@runtime_checkable
class PVLengthable(Protocol):
    """Protocol for refs that can query length."""

    def length(self) -> IntRef:
        """Get container length."""
        ...
