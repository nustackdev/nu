"""Tree layer type definitions and data structures.

This module defines the core types, enums, and data structures used throughout
the tree layer. All data structures are immutable to ensure thread safety and enable safe caching.
"""

from __future__ import annotations

from enum import Enum, IntFlag, auto
from functools import lru_cache
from typing import TYPE_CHECKING, NamedTuple, NewType

from redwood.abc import EMPTY
from redwood.be import (
    ReadAccessProtocol,
    ReadWriteAccessProtocol,
    SnapshotProtocol,
    StorageInterfaceError,
    TransactionProtocol,
    WriteAccessProtocol,
    WriteBatchProtocol,
)


if TYPE_CHECKING:
    from redwood.abc import Empty, TupleKey, Value


__all__ = [
    "ContainerProtocol",
    "ContainerStructure",
    "NodeInfo",
    "NodeType",
    "ParentChainInfo",
    "ParentInfo",
    "require_read_context",
    "require_readwrite_context",
    "require_snapshot",
    "require_transaction",
    "require_write_batch",
    "require_write_context",
]


# ========================================================
# Node types
# ========================================================


class NodeType(Enum):
    """Node type classification in the tree hierarchy.

    Attributes:
        CONTAINER: Node that can have children (internal node)
        PRIMITIVE: Leaf node with a value
        NOT_FOUND: Path does not exist in storage
    """

    PRIMITIVE = auto()
    CONTAINER = auto()
    NOT_FOUND = auto()

    def __str__(self) -> str:
        return self.name


class NodeInfo(NamedTuple):
    """Complete information about a node in the tree.

    This data structure contains all available information about a node,
    including its existence, type, and type-specific attributes.

    Attributes:
        path: Location of the node in the tree
        exists: Whether the node exists in storage
        node_type: Classification of the node (container/primitive/not_found)
        raw_value: Raw value from storage (may be marker or primitive)
        structure: Container structure type (None for primitives)
        protocol: Container protocol flags (None for primitives)
        primitive_value: Actual value for primitives (None for containers)
    """

    path: TupleKey
    exists: bool
    node_type: NodeType
    raw_value: Value | Empty = EMPTY

    # Container-specific fields
    structure: ContainerStructure | None = None
    protocol: ContainerProtocol | None = None

    # Primitive-specific fields
    primitive_value: Value | Empty = EMPTY


class ParentInfo(NamedTuple):
    """Information about a parent node in the tree hierarchy.

    Used when gathering information about the parent chain of a node.

    Attributes:
        path: Location of the parent node
        exists: Whether the parent exists in storage
        structure: Container structure type (None if malformed or missing)
        protocol: Container protocol flags (None if malformed or missing)
        raw_type_data: Raw value from storage (for debugging malformed data)
    """

    path: TupleKey
    exists: bool
    structure: ContainerStructure | None = None
    protocol: ContainerProtocol | None = None
    raw_type_data: Value | Empty = EMPTY


class ParentChainInfo(NamedTuple):
    """Information about the complete parent chain of a node.

    This structure aggregates information about all parents from root to
    immediate parent, categorizing them by their state.

    Attributes:
        chain: Complete parent chain from root to immediate parent
        missing_paths: Paths that don't exist in storage
        malformed_paths: Paths with corrupted or invalid data
    """

    chain: tuple[ParentInfo, ...]
    missing_paths: tuple[TupleKey, ...]
    malformed_paths: tuple[TupleKey, ...]

    @property
    def all_exist(self) -> bool:
        """Check if all parents exist in storage."""
        return len(self.missing_paths) == 0

    @property
    def all_healthy(self) -> bool:
        """Check if all parents have well-formed data."""
        return len(self.malformed_paths) == 0


# ========================================================
# Continer-related types
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

    MUTABLE = 0x01
    SIZED = 0x02
    INDEXED = 0x04

    def __str__(self) -> str:
        parts = []

        if self & self.MUTABLE:
            parts.append("MUTABLE")

        return "|".join(parts)


# ========================================================
# Context protocol typeguards with caching
# ========================================================


@lru_cache(maxsize=2048)
def require_read_context(ctx: object) -> ReadAccessProtocol:
    """Assert that context supports read operations.

    Args:
        ctx: Storage context to check

    Returns:
        The same context, narrowed to ReadAccessProtocol type

    Raises:
        StorageInterfaceError: If context doesn't support read operations

    Example:
        ctx = require_read_context(self.ctx)
        value = ctx.get(path)
    """
    if not isinstance(ctx, ReadAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement read access protocol."
            "This operation requires read access, either a transaction or a snapshot should be used."
        )
    return ctx


@lru_cache(maxsize=2048)
def require_write_context(ctx: object) -> WriteAccessProtocol:
    """Assert that context supports write operations.

    Args:
        ctx: Storage context to check

    Returns:
        The same context, narrowed to WriteAccessProtocol type

    Raises:
        StorageInterfaceError: If context doesn't support write operations

    Example:
        ctx = require_write_context(self.ctx)
        ctx.put(path, value)
    """
    if not isinstance(ctx, WriteAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement write access protocol."
            "This operation requires write access, either a transaction or a write batch should be used."
        )
    return ctx


@lru_cache(maxsize=2048)
def require_readwrite_context(ctx: object) -> ReadWriteAccessProtocol:
    """Assert that context supports both read and write operations.

    Args:
        ctx: Storage context to check

    Returns:
        The same context, narrowed to ReadAccessProtocol & WriteAccessProtocol type

    Raises:
        StorageInterfaceError: If context doesn't support both protocols

    Example:
        ctx = require_readwrite_context(self.ctx)
        old_value = ctx.get(path)
        ctx.put(path, new_value)
    """
    if not isinstance(ctx, ReadWriteAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement either read or write access protocol."
            "This operation requires both read and write access, a transaction should be used."
        )
    return ctx


@lru_cache(maxsize=2048)
def require_transaction(ctx: object) -> TransactionProtocol:
    """Assert that context is a transaction.

    Args:
        ctx: Storage context to check

    Returns:
        The same context, narrowed to TransactionProtocol type

    Raises:
        StorageInterfaceError: If context is not a transaction

    Example:
        ctx = require_transaction(self.ctx)
        ctx.commit()
    """
    if not isinstance(ctx, TransactionProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement transaction protocol. "
            "This operation requires a Transaction context."
        )
    return ctx


@lru_cache(maxsize=2048)
def require_snapshot(ctx: object) -> SnapshotProtocol:
    """Assert that context is a snapshot.

    Args:
        ctx: Storage context to check

    Returns:
        The same context, narrowed to SnapshotProtocol type

    Raises:
        StorageInterfaceError: If context is not a snapshot

    Example:
        ctx = require_snapshot(self.ctx)
        # Use snapshot-specific operations
    """
    if not isinstance(ctx, SnapshotProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement snapshot protocol. "
            "This operation requires a Snapshot context."
        )
    return ctx


@lru_cache(maxsize=2048)
def require_write_batch(ctx: object) -> WriteBatchProtocol:
    """Assert that context is a write batch.

    Args:
        ctx: Storage context to check

    Returns:
        The same context, narrowed to WriteBatchProtocol type

    Raises:
        StorageInterfaceError: If context is not a write batch

    Example:
        ctx = require_write_batch(self.ctx)
        ctx.apply()
    """
    if not isinstance(ctx, WriteBatchProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement write-batch protocol. "
            "This operation requires a WriteBatch context."
        )
    return ctx
