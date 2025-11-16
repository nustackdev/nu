"""Container operations for tree layer.

This module provides container lifecycle management, child operations, and
tree traversal functionality. All operations work directly with storage and
delegate validation to the validation module.
"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, cast

from redwood.loc import key as key_

logger = getLogger(__name__)
from redwood.storage import StorageKeyError, StorageScanOptions
from redwood.types import EMPTY, Empty, Value

from .exceptions import InvalidDepthError, PathExistsError, PathTypeError
from .marker import create_marker, is_marker
from .node_ops import get_node_info, get_node_type
from .types import (
    DEFAULT_PARENT_PROTOCOL,
    DEFAULT_PARENT_STRUCTURE,
    ContainerProtocol,
    ContainerStructure,
    NodeInfo,
    NodeType,
    require_read_context,
    require_readwrite_context,
    require_write_context,
)
from .validation_ops import (
    gather_parent_info,
    validate_compatible,
    validate_is_container,
    validate_is_primitive,
    validate_parents_healthy,
)


if TYPE_CHECKING:
    from collections.abc import Generator

    from redwood.storage import StorageContextType

__all__ = [
    "clear_children",
    "count_children",
    "create_child_container",
    "create_container",
    "create_parents",
    "delete_child",
    "delete_container",
    "delete_subtree",
    "get_child_type",
    "has_child",
    "list_child_keys",
    "list_children",
    "list_descendants",
    "set_child_primitive",
    "walk_tree",
]


# ============================================================================
# CONTAINER LIFECYCLE
# ============================================================================


def create_container(
    path: key_.Key,
    structure: ContainerStructure,
    protocol: ContainerProtocol,
    ctx: StorageContextType,
    *,
    default_parent_structure: ContainerStructure = DEFAULT_PARENT_STRUCTURE,
    default_parent_protocol: ContainerProtocol = DEFAULT_PARENT_PROTOCOL,
    ensure_healthy_parents: bool = True,
) -> bool:
    """Create container at path.

    Args:
        path: Container path
        structure: Container structure ID
        protocol: Container protocol flags
        ctx: Storage context (transaction)
        default_parent_structure: Container structure for parent containers
        default_parent_protocol: Container protocol for parent containers
        ensure_healthy_parents: Validate parents chain, create non-existent parents

    Returns:
        True if created, False if already exists with compatible type

    Raises:
        PathExistsError: If exists with incompatible type
        PathNotFoundError: If parents missing and create_parents=False
        PathTypeError: If type conflicts prevent creation
        StorageInterfaceError: If context doesn't support required operations

    Example:
        >>> create_container(
        ...     ("users", "alice"),
        ...     ContainerStructure(1),
        ...     ContainerProtocol.MUTABLE,
        ...     tx,
        ...     create_parents=True,
        ... )
        True
    """
    # Check if already exists
    node_info = get_node_info(path, ctx)

    # Validate type consistency if node already exists
    if node_info.exists:
        # Primitive check
        if node_info.node_type != NodeType.CONTAINER:
            logger.error(
                "Path exists as primitive, cannot create container",
                extra={"path": path, "node_type": node_info.node_type.name},
            )
            raise PathTypeError(f"Path exists as primitive: {path}")

        # Existing container type compatibility
        try:
            validate_compatible(path, structure, protocol, ctx, node_info=node_info)
            logger.debug(
                "Container already exists with compatible type",
                extra={"path": path, "structure": structure, "protocol": protocol},
            )
            return False  # Already exists with compatible type
        except PathTypeError:
            logger.error(
                "Container exists with incompatible type",
                extra={"path": path, "structure": structure, "protocol": protocol},
            )
            raise PathExistsError(f"Container exists with incompatible type: {path}") from None

    # Ensure parents chain is healthy
    if ensure_healthy_parents:
        parent_info = gather_parent_info(path, ctx)

        # Validate existing parents are healthy
        validate_parents_healthy(path, ctx, parent_info=parent_info)

        # Create missing parents
        if parent_info.missing_paths:
            create_parents(
                path,
                default_parent_structure,
                default_parent_protocol,
                ctx,
            )

    # Create container
    marker = create_marker(structure, protocol)

    wctx = require_write_context(ctx)
    wctx.put(path, marker)

    logger.info(
        "Container created",
        extra={"path": path, "structure": structure, "protocol": protocol},
    )
    return True


def delete_container(
    path: key_.Key,
    ctx: StorageContextType,
) -> bool:
    """Delete container.

    Args:
        path: Container path
        ctx: Storage context (transaction)
        recursive: If True, delete all children first

    Returns:
        True if deleted, False if didn't exist

    Raises:
        PathTypeError: If path is not a container
        StorageInterfaceError: If context doesn't support required operations

    Example:
        >>> delete_container(("users", "alice"), tx, recursive=True)
        True
    """
    info = get_node_info(path, ctx)
    if not info.exists:
        logger.debug("Cannot delete container, path does not exist", extra={"path": path})
        return False

    if info.node_type != NodeType.CONTAINER:
        logger.error(
            "Cannot delete container, path is not a container",
            extra={"path": path, "node_type": info.node_type.name},
        )
        raise PathTypeError(f"Path is not a container: {path}")

    return delete_subtree(path, ctx) > 0


def delete_subtree(path: key_.Key, ctx: StorageContextType) -> int:
    """Delete container and all descendants.

    Args:
        path: Container path
        ctx: Storage context (transaction)

    Returns:
        Number of nodes deleted

    Raises:
        StorageInterfaceError: If context doesn't support required operations

    Example:
        >>> count = delete_subtree(("users", "alice"), tx)
        >>> print(f"Deleted {count} nodes")
    """
    rwctx = require_readwrite_context(ctx)

    # Scan all descendants
    scan_opts = StorageScanOptions(
        start=path,
        start_inclusive=True,
        end=(*path, "\uffff"),
        length=-1,
    )

    deleted_count = 0
    for key in rwctx.scan(scan_opts).keys():
        try:
            rwctx.delete(key)
            deleted_count += 1
        except StorageKeyError:
            pass

    logger.info("Subtree deleted", extra={"path": path, "deleted_count": deleted_count})
    return deleted_count


# ============================================================================
# DIRECT CHILDREN QUERIES
# ============================================================================


def has_child(path: key_.Key, key: key_.KeySegment, ctx: StorageContextType) -> bool:
    """Check if direct child exists.

    Args:
        path: Container path
        key: Child key
        ctx: Storage context (transaction or snapshot)

    Returns:
        True if child exists

    Raises:
        StorageInterfaceError: If context doesn't support read access

    Example:
        >>> has_child(("users", "alice"), "profile", tx)
        True
    """
    child_path = key_.join_segment(path, key)
    child_type = get_node_type(child_path, ctx)
    return child_type != NodeType.NOT_FOUND


def get_child_type(path: key_.Key, key: key_.KeySegment, ctx: StorageContextType) -> NodeType:
    """Get type of direct child.

    Args:
        path: Container path
        key: Child key
        ctx: Storage context (transaction or snapshot)

    Returns:
        NodeType of child

    Raises:
        StorageInterfaceError: If context doesn't support read access

    Example:
        >>> child_type = get_child_type(("users", "alice"), "profile", tx)
        >>> if child_type == NodeType.CONTAINER:
        ...     print("Child is a container")
    """
    child_path = key_.join_segment(path, key)
    return get_node_type(child_path, ctx)


def list_child_keys(
    path: key_.Key, ctx: StorageContextType
) -> Generator[key_.KeySegment, None, None]:
    """List direct child keys only.

    Args:
        path: Container path
        ctx: Storage context (transaction or snapshot)

    Returns:
        List of child keys

    Raises:
        PathNotFoundError: If container doesn't exist
        PathTypeError: If path is not a container
        StorageInterfaceError: If context doesn't support read access

    Example:
        >>> keys = list_child_keys(("users", "alice"), tx)
        >>> print(keys)
        ["profile", "settings", "posts"]
    """
    validate_is_container(path, ctx)

    scan_opts = StorageScanOptions(
        start=path,
        start_inclusive=False,
        end=(*path, "\uffff"),
        length=len(path) + 1,
    )

    for key in require_read_context(ctx).scan(scan_opts).keys():
        yield key[-1]


def list_child_values(path: key_.Key, ctx: StorageContextType) -> Generator[NodeInfo, None, None]:
    """List direct child values only.

    Args:
        path: Container path
        ctx: Storage context (transaction or snapshot)

    Returns:
        List of child values

    Raises:
        PathNotFoundError: If container doesn't exist
        PathTypeError: If path is not a container
        StorageInterfaceError: If context doesn't support read access
    """
    validate_is_container(path, ctx)

    scan_opts = StorageScanOptions(
        start=path,
        start_inclusive=False,
        end=(*path, "\uffff"),
        length=len(path) + 1,
    )

    for key, value in require_read_context(ctx).scan(scan_opts).items():
        yield get_node_info(key, ctx, raw_value=value)


def list_children(
    path: key_.Key, ctx: StorageContextType
) -> Generator[tuple[key_.KeySegment, NodeInfo], None, None]:
    """List all direct children with types.

    Args:
        path: Container path
        ctx: Storage context (transaction or snapshot)

    Returns:
        List of (child_path, node_type) tuples

    Raises:
        PathNotFoundError: If container doesn't exist
        PathTypeError: If path is not a container
        StorageInterfaceError: If context doesn't support read access

    Example:
        >>> children = list_children(("users", "alice"), tx)
        >>> for child_path, node_type in children:
        ...     print(f"{child_path}: {node_type}")
    """
    validate_is_container(path, ctx)

    scan_opts = StorageScanOptions(
        start=path,
        start_inclusive=False,
        end=(*path, "\uffff"),
        length=len(path) + 1,
    )

    for key, value in require_read_context(ctx).scan(scan_opts).items():
        yield (key[-1], get_node_info(key, ctx, raw_value=value))


def count_children(path: key_.Key, ctx: StorageContextType) -> int:
    """Count direct children.

    Args:
        path: Container path
        ctx: Storage context (transaction or snapshot)

    Returns:
        Number of direct children

    Raises:
        PathNotFoundError: If container doesn't exist
        PathTypeError: If path is not a container
        StorageInterfaceError: If context doesn't support read access

    Example:
        >>> count = count_children(("users", "alice"), tx)
        >>> print(f"Container has {count} children")
    """
    validate_is_container(path, ctx)

    scan_opts = StorageScanOptions(
        start=path,
        start_inclusive=False,
        end=(*path, "\uffff"),
        length=len(path) + 1,
    )
    counter = 0
    for _ in require_read_context(ctx).scan(scan_opts).keys():
        counter += 1
    return counter


# ============================================================================
# DIRECT CHILDREN MANIPULATION
# ============================================================================


def create_child_container(
    parent_path: key_.Key,
    key: key_.KeySegment,
    structure: ContainerStructure,
    protocol: ContainerProtocol,
    ctx: StorageContextType,
) -> bool:
    """Create child container.

    Args:
        parent_path: Parent container path
        key: Child key
        structure: Container structure ID
        protocol: Container protocol flags
        ctx: Storage context (transaction)

    Returns:
        True if created, False if already exists

    Raises:
        PathNotFoundError: If parent doesn't exist
        PathTypeError: If parent is not a container
        StorageInterfaceError: If context doesn't support required operations

    Example:
        >>> create_child_container(
        ...     ("users", "alice"),
        ...     "posts",
        ...     ContainerStructure(2),
        ...     ContainerProtocol.MUTABLE,
        ...     tx,
        ... )
        True
    """
    validate_is_container(parent_path, ctx)

    child_path = key_.join_segment(parent_path, key)
    return create_container(child_path, structure, protocol, ctx, ensure_healthy_parents=False)


def set_child_primitive(
    parent_path: key_.Key,
    key: key_.KeySegment,
    value: Value,
    ctx: StorageContextType,
) -> None:
    """Set primitive child value.

    Args:
        parent_path: Parent container path
        key: Child key
        value: Primitive value
        ctx: Storage context (transaction)

    Raises:
        PathNotFoundError: If parent doesn't exist
        PathTypeError: If parent is not a container
        StorageInterfaceError: If context doesn't support required operations

    Example:
        >>> set_child_primitive(("users", "alice"), "name", "Alice Smith", tx)
    """
    validate_is_container(parent_path, ctx)

    child_path = key_.join_segment(parent_path, key)
    child_node_info = get_node_info(child_path, ctx)

    if child_node_info.exists:
        validate_is_primitive(child_path, ctx, node_type=child_node_info.node_type)

    require_write_context(ctx).put(child_path, value)

    logger.debug(
        "Child primitive set",
        extra={
            "parent_path": parent_path,
            "key": key,
            "value_type": type(value).__name__,
            "existed": child_node_info.exists,
        },
    )


def get_child_primitive(
    parent_path: key_.Key,
    key: key_.KeySegment,
    ctx: StorageContextType,
) -> Value | Empty:
    """Get primitive child value.

    Returns the stored primitive value for the given child key, or None if the
    child doesn't exist.

    Raises:
        PathNotFoundError: If parent doesn't exist
        PathTypeError: If parent is not a container or child is a container
        StorageInterfaceError: If context doesn't support read access
    """
    validate_is_container(parent_path, ctx)

    child_path = key_.join_segment(parent_path, key)
    child_node_info = get_node_info(child_path, ctx)

    if not child_node_info.exists:
        return EMPTY

    validate_is_primitive(child_path, ctx, node_type=child_node_info.node_type)

    return cast("Value", child_node_info.primitive_value)


def delete_child(
    parent_path: key_.Key,
    key: key_.KeySegment,
    ctx: StorageContextType,
) -> bool:
    """Delete direct child.

    Args:
        parent_path: Parent container path
        key: Child key
        ctx: Storage context (transaction)
        recursive: If True and child is container, delete subtree

    Returns:
        True if deleted, False if didn't exist

    Raises:
        PathNotFoundError: If parent doesn't exist
        PathTypeError: If parent is not a container
        StorageInterfaceError: If context doesn't support required operations

    Example:
        >>> delete_child(("users", "alice"), "old_profile", tx, recursive=True)
        True
    """
    validate_is_container(parent_path, ctx)

    child_path = key_.join_segment(parent_path, key)
    info = get_node_info(child_path, ctx)

    if not info.exists:
        logger.debug(
            "Cannot delete child, does not exist",
            extra={"parent_path": parent_path, "key": key},
        )
        return False

    if info.node_type == NodeType.CONTAINER:
        deleted = delete_container(child_path, ctx)
    else:
        try:
            require_write_context(ctx).delete(child_path)
            deleted = True
        except StorageKeyError:
            deleted = False

    if deleted:
        logger.debug(
            "Child deleted",
            extra={
                "parent_path": parent_path,
                "key": key,
                "node_type": info.node_type.name,
            },
        )

    return deleted


def clear_children(path: key_.Key, ctx: StorageContextType) -> int:
    """Delete all direct children.

    Args:
        path: Container path
        ctx: Storage context (transaction)

    Returns:
        Number of children deleted

    Raises:
        PathNotFoundError: If container doesn't exist
        PathTypeError: If path is not a container
        StorageInterfaceError: If context doesn't support required operations

    Example:
        >>> count = clear_children(("users", "alice", "temp"), tx)
        >>> print(f"Cleared {count} children")
    """
    count = 0
    for key in list_child_keys(path, ctx):
        if delete_child(path, key, ctx):
            count += 1

    logger.info("Children cleared", extra={"path": path, "cleared_count": count})
    return count


# ============================================================================
# RECURSIVE OPERATIONS
# ============================================================================


def list_descendants(
    path: key_.Key,
    ctx: StorageContextType,
    *,
    depth: int = -1,
) -> Generator[key_.Key, None, None]:
    """List all descendants recursively.

    Args:
        path: Container path
        ctx: Storage context (transaction or snapshot)
        depth: Depth to traverse (-1=unlimited, 1=children, >1 exact depth match)

    Returns:
        List of descendant paths

    Raises:
        PathNotFoundError: If container doesn't exist
        PathTypeError: If path is not a container
        StorageInterfaceError: If context doesn't support read access
        InvalidDepthError: If depth arguments is invalid

    Example:
        >>> descendants = list_descendants(("users", "alice"), tx, depth=2)
        >>> print(f"Found {len(descendants)} descendants at level 2")
    """
    if depth < -2 or depth == 0:
        raise InvalidDepthError(f"Depth argument shoild be either -1 or >= 1. {depth} given")

    rctx = require_read_context(ctx)
    validate_is_container(path, ctx)

    scan_opts = StorageScanOptions(
        start=path,
        end=(*path, "\uffff"),
        length=-1 if depth == -1 else len(path) + depth,
    )

    yield from rctx.scan(scan_opts).keys()


def walk_tree(
    path: key_.Key,
    ctx: StorageContextType,
) -> Generator[tuple[key_.Key, NodeType], None, None]:
    """Iterate over tree structure.

    Args:
        path: Container path
        ctx: Storage context (transaction or snapshot)

    Yields:
        (path, node_type) tuples for each descendant

    Raises:
        PathNotFoundError: If container doesn't exist
        PathTypeError: If path is not a container
        StorageInterfaceError: If context doesn't support read access

    Example:
        >>> for child_path, node_type in walk_tree(("users", "alice"), tx):
        ...     print(f"{child_path}: {node_type}")
    """
    rctx = require_read_context(ctx)
    validate_is_container(path, ctx)

    scan_opts = StorageScanOptions(start=path, end=(*path, "\uffff"), length=-1)

    for key, value in rctx.scan(scan_opts).items():
        node_type = NodeType.CONTAINER if is_marker(value) else NodeType.PRIMITIVE
        yield (key, node_type)


# ============================================================================
# PARENT MANAGEMENT OPERATIONS
# ============================================================================


def create_parents(
    path: key_.Key,
    default_structure: ContainerStructure,
    default_protocol: ContainerProtocol,
    ctx: StorageContextType,
) -> list[key_.Key]:
    """Create all missing parents.

    Creates parent containers for the given path using the specified
    default structure and protocol. Only creates parents that are missing;
    existing parents are left unchanged.

    Args:
        path: Target path
        default_structure: Structure ID for created parents
        default_protocol: Protocol flags for created parents
        ctx: Storage context (transaction)

    Returns:
        List of created parent paths (empty if all existed)

    Raises:
        PathTypeError: If existing parents have malformed data
        StorageInterfaceError: If context doesn't support required operations

    Example:
        >>> created = create_parents(
        ...     ("users", "alice", "profile"),
        ...     ContainerStructure(1),
        ...     ContainerProtocol.MUTABLE,
        ...     tx,
        ... )
        >>> print(f"Created {len(created)} parents: {created}")
    """
    wctx = require_write_context(ctx)

    parent_info = gather_parent_info(path, ctx)

    validate_parents_healthy(path, ctx, parent_info=parent_info)

    if not parent_info.missing_paths:
        return []

    created = []
    for missing_path in parent_info.missing_paths:
        marker = create_marker(default_structure, default_protocol)
        wctx.put(missing_path, marker)
        created.append(missing_path)

    if created:
        logger.info(
            "Missing parents created",
            extra={
                "target_path": path,
                "created_count": len(created),
                "created_paths": created,
            },
        )

    return created
