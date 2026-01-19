"""Container layer type definitions and data structures.

This module defines the core types, enums, and data structures used throughout
the container layer. All data structures are immutable to ensure thread safety and enable safe caching.
"""

from __future__ import annotations

from enum import Enum, IntFlag, auto
from typing import TYPE_CHECKING, NamedTuple, NewType

from everykv.typing import NOT_SET, NotSet


if TYPE_CHECKING:
    from everykv.loc import site as site_
    from everykv.typing import Value


__all__ = [
    "DEFAULT_PARENT_PROTOCOL",
    "DEFAULT_PARENT_STRUCTURE",
    "ContainerProtocol",
    "ContainerStructure",
    "NodeInfo",
    "NodeType",
    "ParentChainInfo",
    "ParentInfo",
]


# ========================================================
# Node types
# ========================================================


class NodeType(Enum):
    """Node type classification in the container hierarchy.

    Attributes:
        CONTAINER: Node that can have children (internal node)
        PRIMITIVE: Leaf node with a value
        NOT_FOUND: Site does not exist in storage
    """

    PRIMITIVE = auto()
    CONTAINER = auto()
    NOT_FOUND = auto()

    def __str__(self) -> str:
        return self.name


class NodeInfo(NamedTuple):
    """Complete information about a node at a site.

    This data structure contains all available information about a node,
    including its existence, type, and type-specific attributes.

    Attributes:
        site: Location of the node
        exists: Whether the node exists in storage
        node_type: Classification of the node (container/primitive/not_found)
        raw_value: Raw value from storage (may be marker or primitive)
        structure: Container structure type (None for primitives)
        protocol: Container protocol flags (None for primitives)
        primitive_value: Actual value for primitives (None for containers)
    """

    site: site_.Site
    exists: bool
    node_type: NodeType
    raw_value: Value | NotSet = NOT_SET

    # Container-specific fields
    structure: ContainerStructure | None = None
    protocol: ContainerProtocol | None = None

    # Primitive-specific fields
    primitive_value: Value | NotSet = NOT_SET


class ParentInfo(NamedTuple):
    """Information about a parent node in the container hierarchy.

    Used when gathering information about the parent chain of a node.

    Attributes:
        site: Location of the parent node
        exists: Whether the parent exists in storage
        structure: Container structure type (None if malformed or missing)
        protocol: Container protocol flags (None if malformed or missing)
        raw_type_data: Raw value from storage (for debugging malformed data)
    """

    site: site_.Site
    exists: bool
    structure: ContainerStructure | None = None
    protocol: ContainerProtocol | None = None
    raw_type_data: Value | NotSet = NOT_SET


class ParentChainInfo(NamedTuple):
    """Information about the complete parent chain of a node.

    This structure aggregates information about all parents from root to
    immediate parent, categorizing them by their state.

    Attributes:
        chain: Complete parent chain from root to immediate parent
        missing_sites: Sites that don't exist in storage
        malformed_sites: Sites with corrupted or invalid data
    """

    chain: tuple[ParentInfo, ...]
    missing_sites: tuple[site_.Site, ...]
    malformed_sites: tuple[site_.Site, ...]

    @property
    def all_exist(self) -> bool:
        """Check if all parents exist in storage."""
        return len(self.missing_sites) == 0

    @property
    def all_healthy(self) -> bool:
        """Check if all parents have well-formed data."""
        return len(self.malformed_sites) == 0


# ========================================================
# Container-related types
# ========================================================

ContainerStructure = NewType("ContainerStructure", int)  # Container structure type: dict, list, etc


class ContainerProtocol(IntFlag):
    """Container behavior flags using bitwise operations.

    Protocol flags define behavioral constraints and capabilities of containers.
    Multiple flags can be combined using bitwise OR operations.

    Important note:
        Protocols don't enforce behavior, they merely act as a hint system for
        debugging, visualization, etc.

    Attributes:
        MUTABLE: Container can be modified after creation
        SIZED: Container keeps track of its children count
        INDEXED: Children maintain insertion order
    """

    NONE = 0
    MUTABLE = 2**0
    SIZED = 2**1
    INDEXED = 2**2
    MAPPING = 2**3
    SET = 2**4

    def __str__(self) -> str:
        parts = []

        if self & self.MUTABLE:
            parts.append("MUTABLE")

        return "|".join(parts)


# Constants

DEFAULT_PARENT_STRUCTURE = ContainerStructure(0)
DEFAULT_PARENT_PROTOCOL = ContainerProtocol.NONE
