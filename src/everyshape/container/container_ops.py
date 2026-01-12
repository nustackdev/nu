"""Container operations for container layer.

This module provides container lifecycle management, child operations, and
traversal functionality. All operations work directly with storage and
delegate validation to the validation module.

All mutations are silent (return None) and idempotent.

Validation is by default enabled for mutation commands and disabled for reads.
"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, cast

from everyshape.storage import LengthFilter, PrefixFilter, StorageScanOptions
from everyshape.types import EMPTY, Empty, Value

from .context import (
    require_read_context,
    require_readwrite_context,
    require_write_context,
)
from .exceptions import ContainerExistsError, ContainerInvalidDepthError, ContainerTypeError
from .marker import create_marker, is_marker
from .node_ops import get_node_info, get_node_type
from .types import (
    DEFAULT_PARENT_PROTOCOL,
    DEFAULT_PARENT_STRUCTURE,
    ContainerProtocol,
    ContainerStructure,
    NodeInfo,
    NodeType,
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

    from everyshape.loc import site as site_
    from everyshape.storage import StorageContextType

__all__ = [
    "clear_children",
    "count_children",
    "create_child_container",
    "create_container",
    "create_parents",
    "delete_child",
    "delete_container",
    "delete_descendants",
    "exists_child",
    "get_child_primitive",
    "get_child_type",
    "iter_child_keys",
    "iter_child_values",
    "iter_children",
    "iter_descendants",
    "put_child_primitive",
    "walk_descendants",
]


logger = getLogger(__name__)

# ============================================================================
# CONTAINER LIFECYCLE
# ============================================================================


def create_container(
    site: site_.Site,
    structure: ContainerStructure,
    protocol: ContainerProtocol,
    ctx: StorageContextType,
    *,
    default_parent_structure: ContainerStructure = DEFAULT_PARENT_STRUCTURE,
    default_parent_protocol: ContainerProtocol = DEFAULT_PARENT_PROTOCOL,
    ensure_healthy_parents: bool = True,
) -> None:
    """Create container at site.

    Idempotent: silent if container already exists with compatible type.

    Args:
        site: Container site
        structure: Container structure ID
        protocol: Container protocol flags
        ctx: Storage context (transaction)
        default_parent_structure: Container structure for parent containers
        default_parent_protocol: Container protocol for parent containers
        ensure_healthy_parents: Validate parents chain, create non-existent parents

    Raises:
        ContainerExistsError: If exists with incompatible type
        ContainerNotFoundError: If parents missing and ensure_healthy_parents=False
        ContainerTypeError: If type conflicts prevent creation
        StorageInterfaceError: If context doesn't support required operations

    Example:
        >>> from everyshape.container import (
        ...     create_container,
        ...     ContainerStructure,
        ...     ContainerProtocol,
        ... )
        >>> # Create a root container with parents auto-created
        >>> create_container(
        ...     ("users", "alice"),
        ...     ContainerStructure(1),
        ...     ContainerProtocol.MUTABLE,
        ...     tx,
        ...     ensure_healthy_parents=True,
        ... )
        >>> # Container at ("users",) is auto-created as parent
    """
    # Check if already exists
    node_info = get_node_info(site, ctx)

    # Validate type consistency if node already exists
    if node_info.exists:
        # Primitive check
        if node_info.node_type != NodeType.CONTAINER:
            logger.error(
                "Site exists as primitive, cannot create container",
                extra={"site": site, "node_type": node_info.node_type.name},
            )
            raise ContainerTypeError(f"Site exists as primitive: {site}")

        # Existing container type compatibility
        try:
            validate_compatible(site, structure, protocol, ctx, node_info=node_info)
            logger.debug(
                "Container already exists with compatible type",
                extra={"site": site, "structure": structure, "protocol": protocol},
            )
            return  # Already exists with compatible type
        except ContainerTypeError:
            logger.error(
                "Container exists with incompatible type",
                extra={"site": site, "structure": structure, "protocol": protocol},
            )
            raise ContainerExistsError(f"Container exists with incompatible type: {site}") from None

    # Ensure parents chain is healthy
    if ensure_healthy_parents:
        parent_info = gather_parent_info(site, ctx)

        # Validate existing parents are healthy
        validate_parents_healthy(site, ctx, parent_info=parent_info)

        # Create missing parents
        if parent_info.missing_sites:
            create_parents(
                site,
                default_parent_structure,
                default_parent_protocol,
                ctx,
            )

    # Create container
    marker = create_marker(structure, protocol)

    wctx = require_write_context(ctx)
    wctx.put(site, marker)

    logger.info(
        "Container created",
        extra={"site": site, "structure": structure, "protocol": protocol},
    )


def delete_container(site: site_.Site, ctx: StorageContextType) -> None:
    """Delete container and all descendants.

    Idempotent: silent if container doesn't exist.

    Args:
        site: Container site
        ctx: Storage context (transaction)

    Raises:
        ContainerTypeError: If site exists but is not a container
        StorageInterfaceError: If context doesn't support required operations
    """
    info = get_node_info(site, ctx)
    if not info.exists:
        logger.debug("Container does not exist, nothing to delete", extra={"site": site})
        return

    if info.node_type != NodeType.CONTAINER:
        logger.error(
            "Cannot delete container, site is not a container",
            extra={"site": site, "node_type": info.node_type.name},
        )
        raise ContainerTypeError(f"Site is not a container: {site}")

    delete_descendants(site, ctx)


def delete_descendants(site: site_.Site, ctx: StorageContextType) -> None:
    """Delete site and all descendants.

    Idempotent: silent if nothing exists at site.

    Args:
        site: Site to delete (with all descendants)
        ctx: Storage context (transaction)

    Raises:
        StorageInterfaceError: If context doesn't support required operations
    """
    rwctx = require_readwrite_context(ctx)

    # Scan all descendants (including site itself)
    prefix = PrefixFilter(prefix=site)
    scan_opts = StorageScanOptions(
        start=site,
        break_filter=prefix,
        filter=prefix,
    )

    for key in rwctx.scan(scan_opts).keys():
        rwctx.delete(key)

    logger.debug("Descendants deleted", extra={"site": site})


# ============================================================================
# DIRECT CHILDREN QUERIES
# ============================================================================


def exists_child(site: site_.Site, key: site_.SiteSegment, ctx: StorageContextType) -> bool:
    """Check if direct child exists.

    Args:
        site: Container site
        key: Child key
        ctx: Storage context (transaction, snapshot or write batch)

    Returns:
        True if child exists

    Raises:
        StorageInterfaceError: If context doesn't support read access

    Example:
        >>> exists_child(("users",), "alice", tx)
        True
        >>> exists_child(("users",), "unknown", tx)
        False
    """
    child_site = (*site, key)
    child_type = get_node_type(child_site, ctx)
    return child_type != NodeType.NOT_FOUND


def get_child_type(site: site_.Site, key: site_.SiteSegment, ctx: StorageContextType) -> NodeType:
    """Get type of direct child.

    Args:
        site: Container site
        key: Child key
        ctx: Storage context (transaction, snapshot or write batch)

    Returns:
        NodeType of child (CONTAINER, PRIMITIVE, or NOT_FOUND)

    Raises:
        StorageInterfaceError: If context doesn't support read access
    """
    child_site = (*site, key)
    return get_node_type(child_site, ctx)


def iter_child_keys(
    site: site_.Site,
    ctx: StorageContextType,
    validate: bool = False,
) -> Generator[site_.SiteSegment, None, None]:
    """Iterate over direct child keys.

    Args:
        site: Container site
        ctx: Storage context (transaction, snapshot or write batch)
        validate: If True, validate site is a container (default False)

    Yields:
        Child keys (last segment of each child site)

    Raises:
        ContainerNotFoundError: If container doesn't exist (when validate=True)
        ContainerTypeError: If site is not a container (when validate=True)
        StorageInterfaceError: If context doesn't support read access

    Example:
        >>> list(iter_child_keys(("users",), tx))
        ["alice", "bob", "charlie"]
    """
    if validate:
        validate_is_container(site, ctx)

    # Direct children: prefix match + length = parent + 1
    prefix = PrefixFilter(prefix=site)
    child_len = LengthFilter(length=len(site) + 1)
    scan_opts = StorageScanOptions(
        start=site,
        break_filter=prefix,
        filter=prefix & child_len,
    )

    for key in require_read_context(ctx).scan(scan_opts).keys():
        yield key[-1]


def iter_child_values(
    site: site_.Site,
    ctx: StorageContextType,
    validate: bool = False,
) -> Generator[NodeInfo, None, None]:
    """Iterate over direct child node info.

    Args:
        site: Container site
        ctx: Storage context (transaction, snapshot or write batch)
        validate: If True, validate site is a container (default False)

    Yields:
        NodeInfo for each direct child

    Raises:
        ContainerNotFoundError: If container doesn't exist (when validate=True)
        ContainerTypeError: If site is not a container (when validate=True)
        StorageInterfaceError: If context doesn't support read access
    """
    if validate:
        validate_is_container(site, ctx)

    # Direct children: prefix match + length = parent + 1
    prefix = PrefixFilter(prefix=site)
    child_len = LengthFilter(length=len(site) + 1)
    scan_opts = StorageScanOptions(
        start=site,
        break_filter=prefix,
        filter=prefix & child_len,
    )

    for key, value in require_read_context(ctx).scan(scan_opts).items():
        yield get_node_info(key, ctx, raw_value=value)


def iter_children(
    site: site_.Site,
    ctx: StorageContextType,
    validate: bool = False,
) -> Generator[tuple[site_.SiteSegment, NodeInfo], None, None]:
    """Iterate over direct children with their info.

    Args:
        site: Container site
        ctx: Storage context (transaction, snapshot or write batch)
        validate: If True, validate site is a container (default False)

    Yields:
        Tuples of (child_key, NodeInfo)

    Raises:
        ContainerNotFoundError: If container doesn't exist (when validate=True)
        ContainerTypeError: If site is not a container (when validate=True)
        StorageInterfaceError: If context doesn't support read access
    """
    if validate:
        validate_is_container(site, ctx)

    # Direct children: prefix match + length = parent + 1
    prefix = PrefixFilter(prefix=site)
    child_len = LengthFilter(length=len(site) + 1)
    scan_opts = StorageScanOptions(
        start=site,
        break_filter=prefix,
        filter=prefix & child_len,
    )

    for key, value in require_read_context(ctx).scan(scan_opts).items():
        yield (key[-1], get_node_info(key, ctx, raw_value=value))


def count_children(
    site: site_.Site,
    ctx: StorageContextType,
    validate: bool = False,
) -> int:
    """Count direct children.

    Args:
        site: Container site
        ctx: Storage context (transaction, snapshot or write batch)
        validate: If True, validate site is a container (default False)

    Returns:
        Number of direct children

    Raises:
        ContainerNotFoundError: If container doesn't exist (when validate=True)
        ContainerTypeError: If site is not a container (when validate=True)
        StorageInterfaceError: If context doesn't support read access
    """
    if validate:
        validate_is_container(site, ctx)

    # Direct children: prefix match + length = parent + 1
    prefix = PrefixFilter(prefix=site)
    child_len = LengthFilter(length=len(site) + 1)
    scan_opts = StorageScanOptions(
        start=site,
        break_filter=prefix,
        filter=prefix & child_len,
    )
    counter = 0
    for _ in require_read_context(ctx).scan(scan_opts).keys():
        counter += 1
    return counter


# ============================================================================
# DIRECT CHILDREN MANIPULATION
# ============================================================================


def create_child_container(
    parent_site: site_.Site,
    key: site_.SiteSegment,
    structure: ContainerStructure,
    protocol: ContainerProtocol,
    ctx: StorageContextType,
    validate: bool = True,
) -> None:
    """Create child container.

    Idempotent: silent if child container already exists with compatible type.

    Args:
        parent_site: Parent container site
        key: Child key
        structure: Container structure ID
        protocol: Container protocol flags
        ctx: Storage context (transaction)
        validate: If True, validate parent is a container (default True)

    Raises:
        ContainerNotFoundError: If parent doesn't exist (when validate=True)
        ContainerTypeError: If parent is not a container (when validate=True)
        StorageInterfaceError: If context doesn't support required operations
    """
    if validate:
        validate_is_container(parent_site, ctx)

    child_site = (*parent_site, key)
    create_container(child_site, structure, protocol, ctx, ensure_healthy_parents=False)


def put_child_primitive(
    parent_site: site_.Site,
    key: site_.SiteSegment,
    value: Value,
    ctx: StorageContextType,
    validate: bool = True,
) -> None:
    """Put primitive child value.

    Idempotent: overwrites if already exists.

    Args:
        parent_site: Parent container site
        key: Child key
        value: Primitive value
        ctx: Storage context (transaction)
        validate: If True, validate parent is a container (default True)

    Raises:
        ContainerNotFoundError: If parent doesn't exist
        ContainerTypeError: If parent is not a container or child is a container
        StorageInterfaceError: If context doesn't support required operations

    Example:
        >>> put_child_primitive(("users",), "alice", {"name": "Alice", "age": 30}, tx)
        >>> get_child_primitive(("users",), "alice", tx)
        {"name": "Alice", "age": 30}
    """
    if validate:
        validate_is_container(parent_site, ctx)

        child_site = (*parent_site, key)
        child_node_info = get_node_info(child_site, ctx)

        if child_node_info.exists:
            validate_is_primitive(child_site, ctx, node_type=child_node_info.node_type)

    child_site = (*parent_site, key)
    require_write_context(ctx).put(child_site, value)

    logger.debug(
        "Child primitive set",
        extra={
            "parent_site": parent_site,
            "key": key,
            "value_type": type(value).__name__,
        },
    )


def get_child_primitive(
    parent_site: site_.Site,
    key: site_.SiteSegment,
    ctx: StorageContextType,
    validate: bool = False,
) -> Value | Empty:
    """Get primitive child value.

    Args:
        parent_site: Parent container site
        key: Child key
        ctx: Storage context (transaction, snapshot or write batch)
        validate: If True, validate parent is a container (default False)

    Returns:
        Primitive value or EMPTY if child doesn't exist

    Raises:
        ContainerNotFoundError: If parent doesn't exist
        ContainerTypeError: If parent is not a container or child is a container
        StorageInterfaceError: If context doesn't support read access
    """
    if validate:
        validate_is_container(parent_site, ctx)

    child_site = (*parent_site, key)
    child_node_info = get_node_info(child_site, ctx)

    if not child_node_info.exists:
        return EMPTY

    validate_is_primitive(child_site, ctx, node_type=child_node_info.node_type)

    return cast("Value", child_node_info.primitive_value)


def delete_child(
    parent_site: site_.Site,
    key: site_.SiteSegment,
    ctx: StorageContextType,
) -> None:
    """Delete direct child.

    Idempotent: silent if child doesn't exist.
    If child is a container, deletes all its descendants too.

    Args:
        parent_site: Parent container site
        key: Child key
        ctx: Storage context (transaction)

    Raises:
        ContainerNotFoundError: If parent doesn't exist
        ContainerTypeError: If parent is not a container
        StorageInterfaceError: If context doesn't support required operations
    """
    validate_is_container(parent_site, ctx)

    child_site = (*parent_site, key)
    info = get_node_info(child_site, ctx)

    if not info.exists:
        logger.debug(
            "Child does not exist, nothing to delete",
            extra={"parent_site": parent_site, "key": key},
        )
        return

    if info.node_type == NodeType.CONTAINER:
        delete_descendants(child_site, ctx)
    else:
        require_write_context(ctx).delete(child_site)

    logger.debug(
        "Child deleted",
        extra={
            "parent_site": parent_site,
            "key": key,
            "node_type": info.node_type.name,
        },
    )


def clear_children(
    site: site_.Site,
    ctx: StorageContextType,
    validate: bool = True,
) -> None:
    """Delete all direct children.

    Idempotent: silent if no children exist.

    Args:
        site: Container site
        ctx: Storage context (transaction)
        validate: If True, validate site is a container (default True)

    Raises:
        ContainerNotFoundError: If container doesn't exist (when validate=True)
        ContainerTypeError: If site is not a container (when validate=True)
        StorageInterfaceError: If context doesn't support required operations
    """
    # Pass validate=False to iter_child_keys since we validate once here
    if validate:
        validate_is_container(site, ctx)

    for key in iter_child_keys(site, ctx, validate=False):
        delete_child(site, key, ctx)

    logger.debug("Children cleared", extra={"site": site})


# ============================================================================
# RECURSIVE OPERATIONS
# ============================================================================


def iter_descendants(
    site: site_.Site,
    ctx: StorageContextType,
    *,
    depth: int = -1,
) -> Generator[site_.Site, None, None]:
    """Iterate over all descendants.

    Args:
        site: Container site
        ctx: Storage context (transaction, snapshot or write batch)
        depth: Depth to traverse (-1=unlimited, 1=children, >1 exact depth match)

    Yields:
        Descendant sites

    Raises:
        ContainerNotFoundError: If container doesn't exist
        ContainerTypeError: If site is not a container
        StorageInterfaceError: If context doesn't support read access
        ContainerInvalidDepthError: If depth argument is invalid

    Example:
        >>> # Get all descendants at any depth
        >>> list(iter_descendants(("users",), tx))
        [("users",), ("users", "alice"), ("users", "alice", "profile"), ("users", "bob")]
        >>> # Get only direct children (depth=1)
        >>> list(iter_descendants(("users",), tx, depth=1))
        [("users", "alice"), ("users", "bob")]
    """
    if depth < -2 or depth == 0:
        raise ContainerInvalidDepthError(
            f"Depth argument should be either -1 or >= 1. {depth} given"
        )

    rctx = require_read_context(ctx)
    validate_is_container(site, ctx)

    # Descendants: prefix match, optionally filter by exact depth
    prefix = PrefixFilter(prefix=site)
    if depth == -1:
        # All descendants at any depth
        scan_opts = StorageScanOptions(
            start=site,
            break_filter=prefix,
            filter=prefix,
        )
    else:
        # Exact depth match
        depth_len = LengthFilter(length=len(site) + depth)
        scan_opts = StorageScanOptions(
            start=site,
            break_filter=prefix,
            filter=prefix & depth_len,
        )

    yield from rctx.scan(scan_opts).keys()


def walk_descendants(
    site: site_.Site,
    ctx: StorageContextType,
) -> Generator[tuple[site_.Site, NodeType], None, None]:
    """Walk over descendant structure.

    Args:
        site: Container site
        ctx: Storage context (transaction, snapshot or write batch)

    Yields:
        Tuples of (site, NodeType) for each descendant

    Raises:
        ContainerNotFoundError: If container doesn't exist
        ContainerTypeError: If site is not a container
        StorageInterfaceError: If context doesn't support read access
    """
    rctx = require_read_context(ctx)
    validate_is_container(site, ctx)

    # All descendants including site itself
    prefix = PrefixFilter(prefix=site)
    scan_opts = StorageScanOptions(
        start=site,
        break_filter=prefix,
        filter=prefix,
    )

    for key, value in rctx.scan(scan_opts).items():
        node_type = NodeType.CONTAINER if is_marker(value) else NodeType.PRIMITIVE
        yield (key, node_type)


# ============================================================================
# PARENT MANAGEMENT OPERATIONS
# ============================================================================


def create_parents(
    site: site_.Site,
    default_structure: ContainerStructure,
    default_protocol: ContainerProtocol,
    ctx: StorageContextType,
) -> None:
    """Create all missing parents.

    Creates parent containers for the given site using the specified
    default structure and protocol. Only creates parents that are missing;
    existing parents are left unchanged.

    Idempotent: silent if all parents already exist.

    Args:
        site: Target site
        default_structure: Structure ID for created parents
        default_protocol: Protocol flags for created parents
        ctx: Storage context (transaction)

    Raises:
        ContainerTypeError: If existing parents have malformed data
        StorageInterfaceError: If context doesn't support required operations
    """
    wctx = require_write_context(ctx)

    parent_info = gather_parent_info(site, ctx)

    validate_parents_healthy(site, ctx, parent_info=parent_info)

    if not parent_info.missing_sites:
        return

    for missing_site in parent_info.missing_sites:
        marker = create_marker(default_structure, default_protocol)
        wctx.put(missing_site, marker)

    logger.debug(
        "Missing parents created",
        extra={
            "target_site": site,
            "created_sites": parent_info.missing_sites,
        },
    )
