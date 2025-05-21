# _constants.py

"""
Constants and type definitions for the state management library.

This module defines the core types, protocols, and enumerations used
throughout the library, establishing a consistent type system.
"""

from __future__ import annotations

from enum import Enum, Flag, auto
from typing import TYPE_CHECKING, TypeVar

from loomi.interfaces.state.state import SyncCallbackFn

if TYPE_CHECKING:
    from ._views.view import BaseView


# Type definitions
PathComponent = str  # A component of a path (string key or integer index)
StatePath = tuple[PathComponent, ...]  # A path represented as a tuple of components
PrimitiveValue = None | bytes | bool | int | float | str  # Basic primitive types
ComplexValue = (
    PrimitiveValue
    | list["ComplexValue"]
    | set["ComplexValue"]
    | tuple["ComplexValue", ...]
    | dict[PathComponent, "ComplexValue"]
)  # Complex types that can be serialized
StateValue = PrimitiveValue | ComplexValue  # Any value that can be stored
StateValueComposite = (
    list[StateValue] | set[StateValue] | tuple[StateValue, ...] | dict[PathComponent, StateValue]
)  # Variant of StateValue that enforces at least one level of nesting
StateCallbackFn = SyncCallbackFn


# Node type enumeration
class NodeType(Enum):
    """Enumeration of possible node types in the state tree."""

    NOT_FOUND = auto()  # Path does not exist
    CONTAINER = auto()  # Container node that can have children
    PRIMITIVE = auto()  # Primitive value node (leaf)

    def __str__(self) -> str:
        return self.name


# Container protocol flags
class ContainerProtocol(Flag):
    """
    Protocol flags defining container capabilities and interfaces.

    Container protocols determine which views and operations are compatible
    with a specific container.
    """

    # Base protocols
    CONTAINER = 1  # Base protocol for all containers

    # Core container types
    MAPPING = 2 | CONTAINER  # Key-based access (dict-like)
    SEQUENCE = 4 | CONTAINER  # Index-based ordered access (list-like)
    SET = 8 | CONTAINER  # Collection of unique values (set-like)

    # Container attributes
    SIZED = auto()  # Has countable size
    ITERABLE = auto()  # Can be iterated over
    MUTABLE = auto()  # Can be modified after creation
    FLAT = auto()  # Can contain only primitives (no nested containers)

    def __str__(self) -> str:
        """Return a string representation of protocols."""
        # Start with base protocols
        parts = []

        # Check for main container types
        if self & ContainerProtocol.MAPPING == ContainerProtocol.MAPPING:
            parts.append("MAPPING")
        elif self & ContainerProtocol.SEQUENCE == ContainerProtocol.SEQUENCE:
            parts.append("SEQUENCE")
        elif self & ContainerProtocol.SET == ContainerProtocol.SET:
            parts.append("SET")
        elif self & ContainerProtocol.CONTAINER == ContainerProtocol.CONTAINER:
            parts.append("CONTAINER")

        # Add attributes
        if self & ContainerProtocol.SIZED:
            parts.append("SIZED")
        if self & ContainerProtocol.ITERABLE:
            parts.append("ITERABLE")
        if self & ContainerProtocol.MUTABLE:
            parts.append("MUTABLE")
        if self & ContainerProtocol.FLAT:
            parts.append("FLAT")

        return "|".join(parts)


# Common protocol combinations
class CommonContainerProtocols:
    """Predefined protocol combinations for common container types."""

    # Standard mutable containers
    DICT = (
        ContainerProtocol.MAPPING
        | ContainerProtocol.SIZED
        | ContainerProtocol.ITERABLE
        | ContainerProtocol.MUTABLE
    )
    LIST = (
        ContainerProtocol.SEQUENCE
        | ContainerProtocol.SIZED
        | ContainerProtocol.ITERABLE
        | ContainerProtocol.MUTABLE
    )
    SET = (
        ContainerProtocol.SET
        | ContainerProtocol.SIZED
        | ContainerProtocol.ITERABLE
        | ContainerProtocol.MUTABLE
    )

    # Read-only variants
    READ_ONLY_DICT = (
        ContainerProtocol.MAPPING | ContainerProtocol.SIZED | ContainerProtocol.ITERABLE
    )
    READ_ONLY_LIST = (
        ContainerProtocol.SEQUENCE | ContainerProtocol.SIZED | ContainerProtocol.ITERABLE
    )
    READ_ONLY_SET = ContainerProtocol.SET | ContainerProtocol.SIZED | ContainerProtocol.ITERABLE

    # Flat variants (primitive-only)
    FLAT_DICT = DICT | ContainerProtocol.FLAT
    FLAT_LIST = LIST | ContainerProtocol.FLAT


# Type variables for view classes
ViewT = TypeVar("ViewT", bound="BaseView")
