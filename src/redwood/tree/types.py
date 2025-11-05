# _constants.py

"""Constants and type definitions for tree storage package.

This module defines the core types, protocols, and enumerations used
throughout the package, establishing a consistent type system.
"""

from __future__ import annotations

from enum import Enum, Flag, auto
from typing import NamedTuple, NewType

from redwood.abc import (
    EMPTY,
    Empty,
    KeyComponent,
    TupleKey,
    Value,
)


__all__ = [
    "ChildInfo",
    "ChildType",
    "ContainerInfo",
    "ContainerProtocol",
    "ContainerState",
    "ContainerStructure",
    "NodeType",
    "ParentInfo",
]


class ChildType(Enum):
    """Simple child type classification."""

    PRIMITIVE = auto()
    CONTAINER = auto()
    NOT_FOUND = auto()


class ChildInfo(NamedTuple):
    """Basic information about a child.

    Using NamedTuple for more efficient initialization than dataclass.
    """

    key: KeyComponent
    exists: bool
    child_type: ChildType
    value: Value | Empty = EMPTY  # For primitives
    stored_structure: ContainerStructure | None = None  # For containers
    stored_protocol: ContainerProtocol | None = None  # For containers


class ParentInfo(NamedTuple):
    """Raw information about a parent container."""

    path: TupleKey
    exists: bool
    stored_structure: ContainerStructure | None = None
    stored_protocol: ContainerProtocol | None = None
    raw_type_data: Value | Empty = EMPTY  # Raw data from storage, could be malformed


class ContainerInfo(NamedTuple):
    """Pure information about container and parent chain - no validation logic."""

    # Container raw data
    exists: bool
    stored_structure: ContainerStructure | None = None
    stored_protocol: ContainerProtocol | None = None
    raw_type_data: Value | Empty = EMPTY  # Raw data from storage, could be malformed

    # Parent chain raw data (from root to immediate parent)
    parents: tuple[ParentInfo, ...] = ()

    # Paths categorization (pure facts, no validation decisions)
    missing_parent_paths: tuple[TupleKey, ...] = ()
    malformed_parent_paths: tuple[TupleKey, ...] = ()


class ContainerState(Enum):
    """Container states after validation."""

    VALID = auto()  # Exists and matches expected type
    NOT_FOUND = auto()  # Doesn't exist
    TYPE_MISMATCH = auto()  # Exists but wrong type
    MALFORMED = auto()  # Exists but corrupted data


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
