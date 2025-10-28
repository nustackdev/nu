"""Container types and information structures."""

from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING, NamedTuple

from redwood.abc import (
    EMPTY,
    Empty,
    KeyComponent,
    TupleKey,
    Value,
)


if TYPE_CHECKING:
    from ..types import (
        ContainerProtocol,
        ContainerStructure,
    )


__all__ = [
    "ChildInfo",
    "ChildType",
    "ContainerInfo",
    "ContainerState",
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
