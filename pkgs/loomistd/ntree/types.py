# _constants.py

"""
Constants and type definitions for tree storage package.

This module defines the core types, protocols, and enumerations used
throughout the package, establishing a consistent type system.
"""

from __future__ import annotations

from enum import Enum, Flag, auto
from typing import TYPE_CHECKING, Any, TypeGuard, TypeVar

from loomi.interfaces.state.state import SyncCallbackFn

if TYPE_CHECKING:
    from .node import BaseNode
    from .transaction import TransactionalBase
    from .view import BaseView


# -------------------------------------------------------------------------
# Type Variables
# -------------------------------------------------------------------------

ViewT = TypeVar("ViewT", bound="BaseView")
TransactionalT = TypeVar("TransactionalT", bound="TransactionalBase")
NodeT = TypeVar("NodeT", bound="BaseNode")

# -------------------------------------------------------------------------
# Primitive Types
# -------------------------------------------------------------------------

# A component of a path in the tree.
PathComponent = str
# A path in the tree, represented as a tuple of components.
PathTuple = tuple[PathComponent, ...]

# Base primitive values that can be stored in the tree.
PrimitiveValue = None | bytes | bool | int | float | str

# Complex values that can be stored in the tree.
ComplexValue = (
    list["PrimitiveValue | ComplexValue"]
    | set["PrimitiveValue | ComplexValue"]
    | tuple["PrimitiveValue | ComplexValue", ...]
    | dict[PathComponent, "PrimitiveValue | ComplexValue"]
)

# Any value that can be stored in the tree.
Value = PrimitiveValue | ComplexValue

# Callback function type for changes.
CallbackFn = SyncCallbackFn


# -------------------------------------------------------------------------
# Node and Container Types
# -------------------------------------------------------------------------


class NodeType(Enum):
    """Enumeration of possible node types in the state tree."""

    NOT_FOUND = auto()  # Path does not exist
    CONTAINER = auto()  # Container node that can have children
    PRIMITIVE = auto()  # Primitive value node (leaf)

    def __str__(self) -> str:
        return self.name


# Container protocol flags
class ContainerStructure(Flag):
    """
    Protocol flags defining container capabilities and interfaces.

    Container protocols determine which views and operations are compatible
    with a specific container.
    """

    # Base protocols
    CONTAINER = 1  # Base protocol for all containers

    # Core container types
    MAPPING_CONTAINER = 2 | CONTAINER  # Key-based access (dict-like)
    SEQUENCE_CONTAINER = 2 << 1 | CONTAINER  # Index-based ordered access (list-like)
    SET_CONTAINER = 2 << 2 | CONTAINER  # Collection of unique values (set-like)
    SERIES_CONTAINER = 2 << 3 | CONTAINER  # Series (timeseries-like)

    def __str__(self) -> str:
        """Return a string representation of protocols."""
        parts = []

        if self & self.CONTAINER:
            parts.append("CONTAINER")
        if self & self.MAPPING_CONTAINER == self.MAPPING_CONTAINER:
            parts.append("MAPPING")
        elif self & self.SEQUENCE_CONTAINER == self.SEQUENCE_CONTAINER:
            parts.append("SEQUENCE")
        elif self & self.SET_CONTAINER == self.SET_CONTAINER:
            parts.append("SET")
        elif self & self.SERIES_CONTAINER == self.SERIES_CONTAINER:
            parts.append("SERIES")

        return " | ".join(parts)


class ContainerProtocol(Flag):
    """
    Container protocols defining container attributes and capabilities.
    These attributes determine how the container can be used and modified.
    """

    # Container protocols
    MUTABLE = 1  # Can be modified after creation
    FLAT = 2 << 1  # Can contain only primitives (no nested containers)

    def __str__(self) -> str:
        parts = []

        if self & self.MUTABLE:
            parts.append("MUTABLE")
        if self & self.FLAT:
            parts.append("FLAT")

        return "|".join(parts)

    # Standard variants
    DICT = MUTABLE
    LIST = MUTABLE
    SET = MUTABLE
    TUPLE = 0

    # Standard variants with flat structure
    FLAT_DICT = DICT | FLAT
    FLAT_LIST = LIST | FLAT
    FLAT_SET = SET | FLAT
    FLAT_TUPLE = TUPLE | FLAT

    # Read-only variants
    READ_ONLY_DICT = DICT ^ MUTABLE
    READ_ONLY_LIST = LIST ^ MUTABLE
    READ_ONLY_SET = SET ^ MUTABLE
    READ_ONLY_TUPLE = TUPLE ^ MUTABLE

    # Read-only variants with flat structure
    READ_ONLY_FLAT_DICT = READ_ONLY_DICT | FLAT
    READ_ONLY_FLAT_LIST = READ_ONLY_LIST | FLAT
    READ_ONLY_FLAT_SET = READ_ONLY_SET | FLAT
    READ_ONLY_FLAT_TUPLE = READ_ONLY_TUPLE | FLAT


# -------------------------------------------------------------------------
# Empty Types (for handling non-existent values in the tree)
# -------------------------------------------------------------------------


class Empty:
    """
    Sentinel object representing an empty value, distinct from None.

    Used for distinguishing between a legitimate None value and a
    nonexistent value in operations that may return None normally.
    """

    def __repr__(self) -> str:
        """String representation for debugging."""
        return "<Empty>"

    def __str__(self) -> str:
        """String representation for display."""
        return "Empty"

    def __bool__(self) -> bool:
        """Boolean evaluation, always False."""
        return False

    def __hash__(self) -> int:
        """Hash value for the Empty sentinel."""
        return hash("Empty")

    def __eq__(self, other: object) -> bool:
        """Equality check, only equal to itself."""
        return isinstance(other, Empty)


def is_empty(value: Any) -> TypeGuard[Empty]:
    """
    Check if a value is the EMPTY sentinel.

    Args:
        value: Value to check

    Returns:
        True if value is the EMPTY sentinel, False otherwise
    """
    return isinstance(value, Empty)


EMPTY = Empty()  # Global instance of the Empty sentinel
