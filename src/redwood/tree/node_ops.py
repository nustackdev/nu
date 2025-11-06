"""Node identification and information gathering.

This module provides core node operations for identifying node types and
gathering information about nodes without performing validation.

Hot path optimizations:
- node_exists: Direct storage check without creating NodeInfo
- get_node_type: Quick type check without full info gathering
- get_node_info: Comprehensive info when needed
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from redwood.be import ReadAccessProtocol, StorageInterfaceError, StorageKeyError

from .marker import extract_marker
from .types import NodeInfo, NodeType


if TYPE_CHECKING:
    from redwood.abc import TupleKey
    from redwood.be import StorageContextType

__all__ = [
    "get_node_info",
    "get_node_type",
    "node_exists",
]


def node_exists(path: TupleKey, ctx: StorageContextType) -> bool:
    """Check if node exists at path.

    Optimized hot path - performs minimal work to determine existence.

    Args:
        path: Path to check
        ctx: Storage context (transaction or snapshot)

    Returns:
        True if node exists, False otherwise

    Example:
        >>> node_exists(("users", "alice"), tx)
        True
    """
    if not isinstance(ctx, ReadAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement read access protocol. Use Snapshot or Transaction to read data from storage."
        )
    try:
        return ctx.has(path)
    except StorageKeyError:
        return False


def get_node_type(path: TupleKey, ctx: StorageContextType) -> NodeType:
    """Get node type without full information gathering.

    Optimized for hot path - determines type without creating full NodeInfo.

    Args:
        path: Path to check
        ctx: Storage context (transaction or snapshot)

    Returns:
        NodeType: CONTAINER, PRIMITIVE, or NOT_FOUND

    Example:
        >>> get_node_type(("users", "alice"), tx)
        <NodeType.CONTAINER>
    """
    if not isinstance(ctx, ReadAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement read access protocol. Use Snapshot or Transaction to read data from storage."
        )
    try:
        raw_value = ctx.get(path)

        # Quick marker check - extract_marker is fast
        if extract_marker(raw_value) is not None:
            return NodeType.CONTAINER

        return NodeType.PRIMITIVE

    except StorageKeyError:
        return NodeType.NOT_FOUND


def get_node_info(path: TupleKey, ctx: StorageContextType) -> NodeInfo:
    """Get complete node information.

    Gathers all available information about a node including type-specific
    attributes. This is the comprehensive version used when full data is needed.

    Args:
        path: Path to gather information about
        ctx: Storage context (transaction or snapshot)

    Returns:
        NodeInfo with all available data:
        - For containers: path, exists=True, node_type=CONTAINER, structure, protocol
        - For primitives: path, exists=True, node_type=PRIMITIVE, primitive_value
        - For missing: path, exists=False, node_type=NOT_FOUND

    Example:
        >>> info = get_node_info(("users", "alice"), tx)
        >>> if info.node_type == NodeType.CONTAINER:
        ...     print(f"Container with structure {info.structure}")
    """
    if not isinstance(ctx, ReadAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement read access protocol. Use Snapshot or Transaction to read data from storage."
        )
    try:
        raw_value = ctx.get(path)

        # Try to parse as container marker
        marker_info = extract_marker(raw_value)
        if marker_info is not None:
            structure, protocol = marker_info
            return NodeInfo(
                path=path,
                exists=True,
                node_type=NodeType.CONTAINER,
                structure=structure,
                protocol=protocol,
            )

        # It's a primitive value
        return NodeInfo(
            path=path,
            exists=True,
            node_type=NodeType.PRIMITIVE,
            primitive_value=raw_value,
        )

    except StorageKeyError:
        # Path doesn't exist
        return NodeInfo(
            path=path,
            exists=False,
            node_type=NodeType.NOT_FOUND,
        )
