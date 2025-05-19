# _constants.py

"""
Constants and type definitions for the state management library.

This module defines the core types, protocols, and enumerations used
throughout the library, establishing a consistent type system.
"""

from enum import Enum, Flag, auto
from typing import Any, Callable, Dict, List, Set, Union


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
    CONTAINER = auto()  # Base protocol for all containers

    # Core container types
    MAPPING = auto() | CONTAINER  # Key-based access (dict-like)
    SEQUENCE = auto() | CONTAINER  # Index-based ordered access (list-like)
    SET = auto() | CONTAINER  # Collection of unique values (set-like)

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


# Type definitions
PathComponent = Union[str, int]  # A component of a path (string key or integer index)
PrimitiveValue = Union[str, int, float, bool, None]  # Basic primitive types
ComplexValue = Union[Dict, List, Set]  # Complex types that can be serialized
StateValue = Union[PrimitiveValue, ComplexValue]  # Any value that can be stored


# Subscription callback type
SubscriptionCallback = Callable[[List[PathComponent], Any, Any], None]
"""
Type for subscription callbacks: (path, old_value, new_value) -> None
"""


# Common protocol combinations
class CommonProtocols:
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
