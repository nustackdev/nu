# _constants.py

"""Constants and type definitions for tree storage package.

This module defines the core types, protocols, and enumerations used
throughout the package, establishing a consistent type system.
"""

from __future__ import annotations

from enum import Enum, Flag, auto
from typing import TYPE_CHECKING, NewType, TypeGuard, TypeVar

from redwood.types import CallbackFn, Value


if TYPE_CHECKING:
    from .context import ContextualBase
    from .node import BaseNode
    from .tree import Tree
    from .view import BaseView

__all__ = [
    "EMPTY",
    "CallbackFn",
    "ContainerProtocol",
    "ContainerStructure",
    "ContextualT",
    "Empty",
    "NodeT",
    "NodeType",
    "PathSegment",
    "TreeT",
    "TuplePath",
    "Value",
    "ViewT",
    "is_empty",
]

# -------------------------------------------------------------------------
# Type Variables
# -------------------------------------------------------------------------

TreeT = TypeVar("TreeT", bound="Tree")
ViewT = TypeVar("ViewT", bound="BaseView")
NodeT = TypeVar("NodeT", bound="BaseNode")
ContextualT = TypeVar("ContextualT", bound="ContextualBase")

# -------------------------------------------------------------------------
# Primitive Types
# -------------------------------------------------------------------------

# A component of a path in the tree.
type PathSegment = str | int
# A path in the tree, represented as a tuple of components.
type TuplePath = tuple[PathSegment, ...]


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
ContainerStructure = NewType("ContainerStructure", int)


class ContainerProtocol(Flag):
    """Container protocols defining container attributes and capabilities."""

    # Container protocols

    MUTABLE = 1  # Can be modified after creation
    # ... Add more protocols as needed

    DEFAULT_PROTOCOL = MUTABLE

    def __str__(self) -> str:
        parts = []

        if self & self.MUTABLE:
            parts.append("MUTABLE")

        return "|".join(parts)


# -------------------------------------------------------------------------
# Empty Types (for handling non-existent values in the tree)
# -------------------------------------------------------------------------


class Empty:
    """Sentinel object representing an empty value, distinct from None.

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


def is_empty(value: object) -> TypeGuard[Empty]:
    """Check if a value is the EMPTY sentinel.

    Args:
        value: Value to check

    Returns:
        True if value is the EMPTY sentinel, False otherwise
    """
    return isinstance(value, Empty)


EMPTY = Empty()  # Global instance of the Empty sentinel
