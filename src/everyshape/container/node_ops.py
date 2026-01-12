"""Node identification and information gathering.

This module provides core node operations for identifying node types and
gathering information about nodes without performing validation.

Hot path optimizations:
- node_exists: Direct storage check without creating NodeInfo
- get_node_type: Quick type check without full info gathering
- get_node_info: Comprehensive info when needed
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from everyshape._types import NOT_SET, NotSet, is_notset
from everyshape.loc import key
from everyshape.types import Empty

from .marker import extract_marker
from .types import NodeInfo, NodeType, ParentChainInfo, ParentInfo, require_read_context


if TYPE_CHECKING:
    from everyshape.storage import StorageContextType
    from everyshape.types import Value

__all__ = [
    "gather_parent_info",
    "get_node_info",
    "get_node_type",
    "node_exists",
]


def node_exists(path: key.Key, ctx: StorageContextType) -> bool:
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
    return require_read_context(ctx).exists(path)


def get_node_type(
    path: key.Key, ctx: StorageContextType, *, raw_value: Value | Empty | NotSet = NOT_SET
) -> NodeType:
    """Get node type without full information gathering.

    Optimized for hot path - determines type without creating full NodeInfo.

    Args:
        path: Path to check
        ctx: Storage context (transaction or snapshot)
        raw_value: Prefetched value to parse info from

    Returns:
        NodeType: CONTAINER, PRIMITIVE, or NOT_FOUND

    Example:
        >>> get_node_type(("users", "alice"), tx)
        <NodeType.CONTAINER>
    """
    if is_notset(raw_value):
        raw_value = require_read_context(ctx).get(path)
        if isinstance(raw_value, Empty):
            return NodeType.NOT_FOUND
        return NodeType.CONTAINER if extract_marker(raw_value) else NodeType.PRIMITIVE
    elif isinstance(raw_value, Empty):
        return NodeType.NOT_FOUND
    else:
        return (
            NodeType.CONTAINER if extract_marker(cast("Value", raw_value)) else NodeType.PRIMITIVE
        )


def get_node_info(
    path: key.Key, ctx: StorageContextType, *, raw_value: Value | Empty | NotSet = NOT_SET
) -> NodeInfo:
    """Get complete node information.

    Gathers all available information about a node including type-specific
    attributes. This is the comprehensive version used when full data is needed.

    Args:
        path: Path to gather information about
        ctx: Storage context (transaction or snapshot)
        raw_value: Prefetched value to parse info from

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
    if is_notset(raw_value):
        raw_value = require_read_context(ctx).get(path)

    # Path doesn't exist
    if isinstance(raw_value, Empty):
        return NodeInfo(
            path=path,
            exists=False,
            node_type=NodeType.NOT_FOUND,
        )

    raw_value = cast("Value", raw_value)

    # Try to parse as container marker
    marker_info = extract_marker(raw_value)
    if marker_info is not None:
        structure, protocol = marker_info
        return NodeInfo(
            path=path,
            exists=True,
            node_type=NodeType.CONTAINER,
            raw_value=raw_value,
            structure=structure,
            protocol=protocol,
        )

    # It's a primitive value
    return NodeInfo(
        path=path,
        exists=True,
        node_type=NodeType.PRIMITIVE,
        raw_value=raw_value,
        primitive_value=raw_value,
    )


def gather_parent_info(path: key.Key, ctx: StorageContextType) -> ParentChainInfo:
    """Gather parent chain information without validation.

    Pure information collection - traverses the path hierarchy from root to
    immediate parent, collecting raw storage data and categorizing paths based
    on existence and data format. Does not make validation decisions.

    Args:
        path: Path to gather parent information for
        ctx: Storage context (transaction or snapshot)

    Returns:
        ParentChainInfo with raw data about parent chain:
        - chain: All parent infos from root to immediate parent
        - missing_paths: Paths that don't exist in storage
        - malformed_paths: Paths with corrupted markers

    Example:
        >>> info = gather_parent_info(("users", "alice", "profile"), tx)
        >>> if info.all_exist and info.all_healthy:
        ...     print("Parent chain is complete and healthy")
    """
    ancestors = key.get_ancestors(path)
    if not ancestors:
        # Root level - no parents
        return ParentChainInfo(
            chain=(),
            missing_paths=(),
            malformed_paths=(),
        )

    parent_infos = []
    missing_paths = []
    malformed_paths = []

    for ancestor_path in ancestors:
        info = get_node_info(ancestor_path, ctx)

        if not info.exists:
            parent_info = ParentInfo(
                path=ancestor_path,
                exists=False,
            )
            parent_infos.append(parent_info)
            missing_paths.append(ancestor_path)

        elif info.node_type == NodeType.CONTAINER:
            # Check if marker is well-formed
            if info.structure is None or info.protocol is None:
                parent_info = ParentInfo(
                    path=ancestor_path,
                    exists=True,
                    structure=None,
                    protocol=None,
                    raw_type_data=None,  # Malformed
                )
                parent_infos.append(parent_info)
                malformed_paths.append(ancestor_path)
            else:
                parent_info = ParentInfo(
                    path=ancestor_path,
                    exists=True,
                    structure=info.structure,
                    protocol=info.protocol,
                    raw_type_data=None,
                )
                parent_infos.append(parent_info)

        else:
            # Primitive at parent location - malformed
            parent_info = ParentInfo(
                path=ancestor_path,
                exists=True,
                structure=None,
                protocol=None,
                raw_type_data=info.primitive_value,
            )
            parent_infos.append(parent_info)
            malformed_paths.append(ancestor_path)

    return ParentChainInfo(
        chain=tuple(parent_infos),
        missing_paths=tuple(missing_paths),
        malformed_paths=tuple(malformed_paths),
    )
