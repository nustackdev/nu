"""Validation layer for tree operations.

This module enforces tree rules and constraints, providing both information
gathering and validation functions. Information functions gather data without
making validation decisions, while validation functions check conditions and
raise exceptions on failure.
"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from .exceptions import PathExistsError, PathNotFoundError, PathTypeError
from .node_ops import gather_parent_info, get_node_info, get_node_type
from .types import ContainerProtocol, ContainerStructure, NodeInfo, NodeType, ParentChainInfo


if TYPE_CHECKING:
    from redwood.loc import key
    from redwood.storage import StorageContextType

__all__ = [
    "validate_compatible",
    "validate_exists",
    "validate_is_container",
    "validate_is_primitive",
    "validate_not_exists",
    "validate_parents_chain",
    "validate_parents_exist",
    "validate_parents_healthy",
]

logger = getLogger(__name__)


def validate_exists(
    path: key.Key, ctx: StorageContextType, *, node_type: NodeType | None = None
) -> None:
    """Validate that node exists at path.

    Args:
        path: Path to validate
        ctx: Storage context (transaction or snapshot)
        node_type: Prefetched node type (optional)

    Raises:
        PathNotFoundError: If node does not exist

    Example:
        >>> validate_exists(("users", "alice"), tx)  # Raises if not found
    """
    node_type = get_node_type(path, ctx) if node_type is None else node_type
    if node_type == NodeType.NOT_FOUND:
        logger.warning("Validation failed: path does not exist", extra={"path": path})
        raise PathNotFoundError(f"Path does not exist: {path}")


def validate_not_exists(
    path: key.Key, ctx: StorageContextType, *, node_type: NodeType | None = None
) -> None:
    """Validate that node does not exist at path.

    Args:
        path: Path to validate
        ctx: Storage context (transaction or snapshot)
        node_type: Prefetched node type (optional)

    Raises:
        PathExistsError: If node already exists

    Example:
        >>> validate_not_exists(("users", "new_user"), tx)  # Raises if exists
    """
    node_type = get_node_type(path, ctx) if node_type is None else node_type
    if node_type != NodeType.NOT_FOUND:
        logger.warning(
            "Validation failed: path already exists",
            extra={"path": path, "node_type": node_type.name},
        )
        raise PathExistsError(f"Path already exists: {path}")


def validate_is_container(
    path: key.Key, ctx: StorageContextType, *, node_type: NodeType | None = None
) -> None:
    """Validate that path is a container.

    Args:
        path: Path to validate
        ctx: Storage context (transaction or snapshot)
        node_type: Prefetched node type (optional)

    Raises:
        PathNotFoundError: If path does not exist
        PathTypeError: If path is not a container

    Example:
        >>> validate_is_container(("users",), tx)  # Raises if not container
    """
    node_type = get_node_type(path, ctx) if node_type is None else node_type
    if node_type == NodeType.NOT_FOUND:
        logger.warning("Validation failed: path does not exist", extra={"path": path})
        raise PathNotFoundError(f"Path does not exist: {path}")
    if node_type != NodeType.CONTAINER:
        logger.warning(
            "Validation failed: path is not a container",
            extra={"path": path, "actual_type": node_type.name},
        )
        raise PathTypeError(f"Path is not a container: {path}")


def validate_is_primitive(
    path: key.Key, ctx: StorageContextType, *, node_type: NodeType | None = None
) -> None:
    """Validate that path is a primitive value.

    Args:
        path: Path to validate
        ctx: Storage context (transaction or snapshot)
        node_type: Prefetched node type (optional)

    Raises:
        PathNotFoundError: If path does not exist
        PathTypeError: If path is not a primitive

    Example:
        >>> validate_is_primitive(("users", "alice", "name"), tx)  # Raises if not primitive
    """
    node_type = get_node_type(path, ctx) if node_type is None else node_type
    if node_type == NodeType.NOT_FOUND:
        logger.warning("Validation failed: path does not exist", extra={"path": path})
        raise PathNotFoundError(f"Path does not exist: {path}")
    if node_type != NodeType.PRIMITIVE:
        logger.warning(
            "Validation failed: path is not a primitive",
            extra={"path": path, "actual_type": node_type.name},
        )
        raise PathTypeError(f"Path is not a primitive: {path}")


def validate_parents_exist(
    path: key.Key, ctx: StorageContextType, *, parent_info: ParentChainInfo | None = None
) -> None:
    """Validate that all parent containers exist.

    Args:
        path: Path to validate parents for
        ctx: Storage context (transaction or snapshot)
        parent_info: Prefetched parent chain info (optional)

    Raises:
        PathNotFoundError: If any parent containers are missing

    Example:
        >>> validate_parents_exist(("users", "alice", "profile"), tx)
    """
    parent_info = gather_parent_info(path, ctx) if parent_info is None else parent_info
    if not parent_info.all_exist:
        logger.warning(
            "Validation failed: missing parent containers",
            extra={"path": path, "missing_paths": parent_info.missing_paths},
        )
        raise PathNotFoundError(f"Missing parent containers: {parent_info.missing_paths}")


def validate_parents_healthy(
    path: key.Key, ctx: StorageContextType, *, parent_info: ParentChainInfo | None = None
) -> None:
    """Validate that all parent containers have well-formed markers.

    Args:
        path: Path to validate parents for
        ctx: Storage context (transaction or snapshot)
        parent_info: Prefetched parent chain info (optional)

    Raises:
        PathTypeError: If any parent containers have malformed data

    Example:
        >>> validate_parents_healthy(("users", "alice", "profile"), tx)
    """
    parent_info = gather_parent_info(path, ctx) if parent_info is None else parent_info
    if not parent_info.all_healthy:
        logger.error(
            "Validation failed: malformed parent containers",
            extra={"path": path, "malformed_paths": parent_info.malformed_paths},
        )
        raise PathTypeError(f"Malformed parent containers: {parent_info.malformed_paths}")


def validate_parents_chain(
    path: key.Key, ctx: StorageContextType, *, parent_info: ParentChainInfo | None = None
) -> None:
    """Validate complete parent chain (existence + health).

    Combines existence and health checks to ensure all parents exist
    and have well-formed data.

    Args:
        path: Path to validate parents for
        ctx: Storage context (transaction or snapshot)
        parent_info: Prefetched parent chain info (optional)

    Raises:
        PathNotFoundError: If any parent containers are missing
        PathTypeError: If any parent containers have malformed data

    Example:
        >>> validate_parents_chain(("users", "alice", "profile"), tx)
    """
    parent_info = gather_parent_info(path, ctx) if parent_info is None else parent_info

    if not parent_info.all_exist:
        logger.warning(
            "Validation failed: parent chain broken, missing containers",
            extra={"path": path, "missing_paths": parent_info.missing_paths},
        )
        raise PathNotFoundError(f"Missing parent containers: {parent_info.missing_paths}")

    if not parent_info.all_healthy:
        logger.error(
            "Validation failed: parent chain broken, malformed containers",
            extra={"path": path, "malformed_paths": parent_info.malformed_paths},
        )
        raise PathTypeError(f"Malformed parent containers: {parent_info.malformed_paths}")


def validate_compatible(
    path: key.Key,
    expected_structure: ContainerStructure,
    expected_protocol: ContainerProtocol,
    ctx: StorageContextType,
    *,
    node_info: NodeInfo | None = None,
) -> None:
    """Validate container type matches expectations.

    Checks that container exists, has well-formed data, and matches
    expected structure and protocol. Protocol matching uses bitwise AND
    to allow subset matching.

    Args:
        path: Container path to validate
        expected_structure: Required structure ID
        expected_protocol: Required protocol flags (bitwise match)
        ctx: Storage context (transaction or snapshot)
        node_info: Prefetched node info (optional)

    Raises:
        PathNotFoundError: If container doesn't exist
        PathTypeError: If type mismatch or malformed data

    Example:
        >>> validate_compatible(
        ...     ("users",), ContainerStructure(1), ContainerProtocol.MUTABLE, tx
        ... )
    """
    node_info = get_node_info(path, ctx) if node_info is None else node_info

    if not node_info.exists:
        logger.warning("Validation failed: container does not exist", extra={"path": path})
        raise PathNotFoundError(f"Container does not exist: {path}")

    if node_info.node_type != NodeType.CONTAINER:
        logger.warning(
            "Validation failed: path is not a container",
            extra={"path": path, "actual_type": node_info.node_type.name},
        )
        raise PathTypeError(f"Path is not a container: {path}")

    if node_info.structure is None or node_info.protocol is None:
        logger.error(
            "Validation failed: container has malformed data",
            extra={"path": path, "structure": node_info.structure, "protocol": node_info.protocol},
        )
        raise PathTypeError(f"Container has malformed data: {path}")

    # Structure must match exactly
    if node_info.structure != expected_structure:
        logger.warning(
            "Validation failed: structure mismatch",
            extra={
                "path": path,
                "expected_structure": expected_structure,
                "actual_structure": node_info.structure,
            },
        )
        raise PathTypeError(
            f"Structure mismatch at {path}: expected {expected_structure}, got {node_info.structure}"
        )

    # Protocol must have at least one common flag
    if not (expected_protocol & node_info.protocol):
        logger.warning(
            "Validation failed: protocol mismatch",
            extra={
                "path": path,
                "expected_protocol": expected_protocol,
                "actual_protocol": node_info.protocol,
            },
        )
        raise PathTypeError(
            f"Protocol mismatch at {path}: expected {expected_protocol}, got {node_info.protocol}"
        )
