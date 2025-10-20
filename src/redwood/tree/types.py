# _constants.py

"""Constants and type definitions for tree storage package.

This module defines the core types, protocols, and enumerations used
throughout the package, establishing a consistent type system.
"""

from __future__ import annotations

from enum import Enum, Flag, auto
from typing import NewType


__all__ = [
    "ContainerProtocol",
    "ContainerStructure",
    "NodeType",
]


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
