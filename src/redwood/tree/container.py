"""Container operations for tree layer.

This module provides container lifecycle management, child operations, and
tree traversal functionality. All operations work directly with storage and
delegate validation to the validation module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from redwood.be import (
    ReadAccessProtocol,
    StorageInterfaceError,
    StorageKeyError,
    StorageScanOptions,
    WriteAccessProtocol,
)

from .exceptions import PathExistsError, PathTypeError
from .marker import create_marker, is_marker
from .navigation import join_path
from .node import get_node_info, get_node_type
from .types import ContainerProtocol, ContainerStructure, NodeType
from .validation import (
    gather_parent_info,
    validate_compatible,
    validate_is_container,
    validate_parents_chain,
    validate_parents_healthy,
)


if TYPE_CHECKING:
    from collections.abc import Generator

    from redwood.abc import KeyComponent, TupleKey, Value
    from redwood.be import StorageContextType

__all__ = [
    "clear_children",
    "count_children",
    "create_child_container",
    "create_container",
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
    path: TupleKey,
    structure: ContainerStructure,
    protocol: ContainerProtocol,
    ctx: StorageContextType,
    *,
    create_parents: bool = True,
) -> bool:
    """Create container at path.

    Args:
        path: Container path
        structure: Container structure ID
        protocol: Container protocol flags
        ctx: Storage context (transaction)
        create_parents: Whether to create missing parents

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
    if not isinstance(ctx, ReadAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement read access protocol. "
            "Use Snapshot or Transaction to read data from storage."
        )

    if not isinstance(ctx, WriteAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement write access protocol. "
            "Use Transaction to write data to storage."
        )

    # Check if already exists
    info = get_node_info(path, ctx)
    if info.exists:
        if info.node_type != NodeType.CONTAINER:
            raise PathTypeError(f"Path exists as primitive: {path}")
        # Check compatibility
        try:
            validate_compatible(path, structure, protocol, ctx)
            return False  # Already exists with compatible type
        except PathTypeError:
            raise PathExistsError(f"Container exists with incompatible type: {path}") from None

    # Validate/create parents
    if create_parents:
        validate_parents_healthy(path, ctx)

        parent_info = gather_parent_info(path, ctx)
        if not parent_info.all_exist:
            # Create missing parents with default type
            for missing_path in parent_info.missing_paths:
                marker = create_marker(
                    ContainerStructure(1),  # Default associative
                    ContainerProtocol.MUTABLE,
                )
                ctx.put(missing_path, marker)
    else:
        validate_parents_chain(path, ctx)

    # Create container
    marker = create_marker(structure, protocol)
    ctx.put(path, marker)
    return True


def delete_container(
    path: TupleKey,
    ctx: StorageContextType,
    *,
    recursive: bool = False,
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
    if not isinstance(ctx, ReadAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement read access protocol. "
            "Use Snapshot or Transaction to read data from storage."
        )

    if not isinstance(ctx, WriteAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement write access protocol. "
            "Use Transaction to write data to storage."
        )

    info = get_node_info(path, ctx)
    if not info.exists:
        return False

    if info.node_type != NodeType.CONTAINER:
        raise PathTypeError(f"Path is not a container: {path}")

    if recursive:
        delete_subtree(path, ctx)
    else:
        # Just delete the container marker
        try:
            ctx.delete(path)
            return True
        except StorageKeyError:
            return False

    return True


def delete_subtree(path: TupleKey, ctx: StorageContextType) -> int:
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
    if not isinstance(ctx, ReadAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement read access protocol. "
            "Use Snapshot or Transaction to read data from storage."
        )

    if not isinstance(ctx, WriteAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement write access protocol. "
            "Use Transaction to write data to storage."
        )

    # Scan all descendants
    start_key = (*path, "")
    end_key = (*path, "\uffff")

    scan_opts = StorageScanOptions(start=start_key, end=end_key)
    keys_to_delete = [path]

    for key, _ in ctx.scan(scan_opts).items():
        keys_to_delete.append(key)

    # Delete all
    deleted_count = 0
    for key in keys_to_delete:
        try:
            ctx.delete(key)
            deleted_count += 1
        except StorageKeyError:
            pass

    return deleted_count


# ============================================================================
# DIRECT CHILDREN QUERIES
# ============================================================================


def has_child(path: TupleKey, key: KeyComponent, ctx: StorageContextType) -> bool:
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
    if not isinstance(ctx, ReadAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement read access protocol. "
            "Use Snapshot or Transaction to read data from storage."
        )

    child_path = join_path(path, key)
    child_type = get_node_type(child_path, ctx)
    return child_type != NodeType.NOT_FOUND


def get_child_type(path: TupleKey, key: KeyComponent, ctx: StorageContextType) -> NodeType:
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
    if not isinstance(ctx, ReadAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement read access protocol. "
            "Use Snapshot or Transaction to read data from storage."
        )

    child_path = join_path(path, key)
    return get_node_type(child_path, ctx)


def list_child_keys(path: TupleKey, ctx: StorageContextType) -> list[KeyComponent]:
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
    if not isinstance(ctx, ReadAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement read access protocol. "
            "Use Snapshot or Transaction to read data from storage."
        )

    validate_is_container(path, ctx)

    start_key = (*path, "")
    end_key = (*path, "\uffff")
    target_depth = len(path) + 1

    scan_opts = StorageScanOptions(start=start_key, end=end_key)
    keys = []

    for key, _ in ctx.scan(scan_opts).items():
        if len(key) == target_depth:
            keys.append(key[-1])

    return keys


def list_children(path: TupleKey, ctx: StorageContextType) -> list[tuple[TupleKey, NodeType]]:
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
    if not isinstance(ctx, ReadAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement read access protocol. "
            "Use Snapshot or Transaction to read data from storage."
        )

    validate_is_container(path, ctx)

    start_key = (*path, "")
    end_key = (*path, "\uffff")
    target_depth = len(path) + 1

    scan_opts = StorageScanOptions(start=start_key, end=end_key)
    children = []

    for key, value in ctx.scan(scan_opts).items():
        if len(key) == target_depth:
            node_type = NodeType.CONTAINER if is_marker(value) else NodeType.PRIMITIVE
            children.append((key, node_type))

    return children


def count_children(path: TupleKey, ctx: StorageContextType) -> int:
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
    if not isinstance(ctx, ReadAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement read access protocol. "
            "Use Snapshot or Transaction to read data from storage."
        )

    return len(list_child_keys(path, ctx))


# ============================================================================
# DIRECT CHILDREN MANIPULATION
# ============================================================================


def create_child_container(
    parent_path: TupleKey,
    key: KeyComponent,
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
    if not isinstance(ctx, ReadAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement read access protocol. "
            "Use Snapshot or Transaction to read data from storage."
        )

    if not isinstance(ctx, WriteAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement write access protocol. "
            "Use Transaction to write data to storage."
        )

    validate_is_container(parent_path, ctx)

    child_path = join_path(parent_path, key)
    return create_container(child_path, structure, protocol, ctx, create_parents=False)


def set_child_primitive(
    parent_path: TupleKey,
    key: KeyComponent,
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
    if not isinstance(ctx, ReadAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement read access protocol. "
            "Use Snapshot or Transaction to read data from storage."
        )

    if not isinstance(ctx, WriteAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement write access protocol. "
            "Use Transaction to write data to storage."
        )

    validate_is_container(parent_path, ctx)

    child_path = join_path(parent_path, key)
    ctx.put(child_path, value)


def delete_child(
    parent_path: TupleKey,
    key: KeyComponent,
    ctx: StorageContextType,
    *,
    recursive: bool = False,
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
    if not isinstance(ctx, ReadAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement read access protocol. "
            "Use Snapshot or Transaction to read data from storage."
        )

    if not isinstance(ctx, WriteAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement write access protocol. "
            "Use Transaction to write data to storage."
        )

    validate_is_container(parent_path, ctx)

    child_path = join_path(parent_path, key)
    info = get_node_info(child_path, ctx)

    if not info.exists:
        return False

    if info.node_type == NodeType.CONTAINER:
        return delete_container(child_path, ctx, recursive=recursive)
    else:
        try:
            ctx.delete(child_path)
            return True
        except StorageKeyError:
            return False


def clear_children(path: TupleKey, ctx: StorageContextType) -> int:
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
    if not isinstance(ctx, ReadAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement read access protocol. "
            "Use Snapshot or Transaction to read data from storage."
        )

    if not isinstance(ctx, WriteAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement write access protocol. "
            "Use Transaction to write data to storage."
        )

    keys = list_child_keys(path, ctx)
    count = 0
    for key in keys:
        if delete_child(path, key, ctx, recursive=True):
            count += 1
    return count


# ============================================================================
# RECURSIVE OPERATIONS
# ============================================================================


def list_descendants(
    path: TupleKey,
    ctx: StorageContextType,
    *,
    max_depth: int | None = None,
) -> list[TupleKey]:
    """List all descendants recursively.

    Args:
        path: Container path
        ctx: Storage context (transaction or snapshot)
        max_depth: Maximum depth to traverse (None = unlimited)

    Returns:
        List of descendant paths

    Raises:
        PathNotFoundError: If container doesn't exist
        PathTypeError: If path is not a container
        StorageInterfaceError: If context doesn't support read access

    Example:
        >>> descendants = list_descendants(("users", "alice"), tx, max_depth=2)
        >>> print(f"Found {len(descendants)} descendants")
    """
    if not isinstance(ctx, ReadAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement read access protocol. "
            "Use Snapshot or Transaction to read data from storage."
        )

    validate_is_container(path, ctx)

    start_key = (*path, "")
    end_key = (*path, "\uffff")

    scan_opts = StorageScanOptions(start=start_key, end=end_key)
    descendants = []
    base_depth = len(path)

    for key, _ in ctx.scan(scan_opts).items():
        if max_depth is None or (len(key) - base_depth) <= max_depth:
            descendants.append(key)

    return descendants


def walk_tree(
    path: TupleKey,
    ctx: StorageContextType,
    *,
    depth_first: bool = True,
) -> Generator[tuple[TupleKey, NodeType], None, None]:
    """Iterate over tree structure.

    Args:
        path: Container path
        ctx: Storage context (transaction or snapshot)
        depth_first: If True, use depth-first traversal (unused currently)

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
    if not isinstance(ctx, ReadAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement read access protocol. "
            "Use Snapshot or Transaction to read data from storage."
        )

    validate_is_container(path, ctx)

    start_key = (*path, "")
    end_key = (*path, "\uffff")

    scan_opts = StorageScanOptions(start=start_key, end=end_key)

    for key, value in ctx.scan(scan_opts).items():
        node_type = NodeType.CONTAINER if is_marker(value) else NodeType.PRIMITIVE
        yield (key, node_type)
