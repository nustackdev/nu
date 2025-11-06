"""Validation layer for tree operations.

This module enforces tree rules and constraints, providing both information
gathering and validation functions. Information functions gather data without
making validation decisions, while validation functions check conditions and
raise exceptions on failure.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from redwood.be import ReadAccessProtocol, StorageInterfaceError

from .exceptions import PathNotFoundError, PathTypeError
from .navigation import get_ancestors
from .node_ops import get_node_info, get_node_type
from .types import ContainerProtocol, ContainerStructure, NodeType, ParentChainInfo, ParentInfo


if TYPE_CHECKING:
    from redwood.abc import TupleKey
    from redwood.be import StorageContextType

__all__ = [
    "gather_parent_info",
    "validate_compatible",
    "validate_exists",
    "validate_is_container",
    "validate_is_primitive",
    "validate_not_exists",
    "validate_parents_chain",
    "validate_parents_exist",
    "validate_parents_healthy",
]


def gather_parent_info(path: TupleKey, ctx: StorageContextType) -> ParentChainInfo:
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
    if not isinstance(ctx, ReadAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement read access protocol. "
            "Use Snapshot or Transaction to read data from storage."
        )

    ancestors = get_ancestors(path)
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


def validate_exists(path: TupleKey, ctx: StorageContextType) -> None:
    """Validate that node exists at path.

    Args:
        path: Path to validate
        ctx: Storage context (transaction or snapshot)

    Raises:
        PathNotFoundError: If node does not exist

    Example:
        >>> validate_exists(("users", "alice"), tx)  # Raises if not found
    """
    if not isinstance(ctx, ReadAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement read access protocol. "
            "Use Snapshot or Transaction to read data from storage."
        )

    node_type = get_node_type(path, ctx)
    if node_type == NodeType.NOT_FOUND:
        raise PathNotFoundError(f"Path does not exist: {path}")


def validate_not_exists(path: TupleKey, ctx: StorageContextType) -> None:
    """Validate that node does not exist at path.

    Args:
        path: Path to validate
        ctx: Storage context (transaction or snapshot)

    Raises:
        PathExistsError: If node already exists

    Example:
        >>> validate_not_exists(("users", "new_user"), tx)  # Raises if exists
    """
    if not isinstance(ctx, ReadAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement read access protocol. "
            "Use Snapshot or Transaction to read data from storage."
        )

    from .exceptions import PathExistsError

    node_type = get_node_type(path, ctx)
    if node_type != NodeType.NOT_FOUND:
        raise PathExistsError(f"Path already exists: {path}")


def validate_is_container(path: TupleKey, ctx: StorageContextType) -> None:
    """Validate that path is a container.

    Args:
        path: Path to validate
        ctx: Storage context (transaction or snapshot)

    Raises:
        PathNotFoundError: If path does not exist
        PathTypeError: If path is not a container

    Example:
        >>> validate_is_container(("users",), tx)  # Raises if not container
    """
    if not isinstance(ctx, ReadAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement read access protocol. "
            "Use Snapshot or Transaction to read data from storage."
        )

    node_type = get_node_type(path, ctx)
    if node_type == NodeType.NOT_FOUND:
        raise PathNotFoundError(f"Path does not exist: {path}")
    if node_type != NodeType.CONTAINER:
        raise PathTypeError(f"Path is not a container: {path}")


def validate_is_primitive(path: TupleKey, ctx: StorageContextType) -> None:
    """Validate that path is a primitive value.

    Args:
        path: Path to validate
        ctx: Storage context (transaction or snapshot)

    Raises:
        PathNotFoundError: If path does not exist
        PathTypeError: If path is not a primitive

    Example:
        >>> validate_is_primitive(("users", "alice", "name"), tx)  # Raises if not primitive
    """
    if not isinstance(ctx, ReadAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement read access protocol. "
            "Use Snapshot or Transaction to read data from storage."
        )

    node_type = get_node_type(path, ctx)
    if node_type == NodeType.NOT_FOUND:
        raise PathNotFoundError(f"Path does not exist: {path}")
    if node_type != NodeType.PRIMITIVE:
        raise PathTypeError(f"Path is not a primitive: {path}")


def validate_parents_exist(path: TupleKey, ctx: StorageContextType) -> None:
    """Validate that all parent containers exist.

    Args:
        path: Path to validate parents for
        ctx: Storage context (transaction or snapshot)

    Raises:
        PathNotFoundError: If any parent containers are missing

    Example:
        >>> validate_parents_exist(("users", "alice", "profile"), tx)
    """
    if not isinstance(ctx, ReadAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement read access protocol. "
            "Use Snapshot or Transaction to read data from storage."
        )

    parent_info = gather_parent_info(path, ctx)
    if not parent_info.all_exist:
        raise PathNotFoundError(f"Missing parent containers: {parent_info.missing_paths}")


def validate_parents_healthy(path: TupleKey, ctx: StorageContextType) -> None:
    """Validate that all parent containers have well-formed markers.

    Args:
        path: Path to validate parents for
        ctx: Storage context (transaction or snapshot)

    Raises:
        PathTypeError: If any parent containers have malformed data

    Example:
        >>> validate_parents_healthy(("users", "alice", "profile"), tx)
    """
    if not isinstance(ctx, ReadAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement read access protocol. "
            "Use Snapshot or Transaction to read data from storage."
        )

    parent_info = gather_parent_info(path, ctx)
    if not parent_info.all_healthy:
        raise PathTypeError(f"Malformed parent containers: {parent_info.malformed_paths}")


def validate_parents_chain(path: TupleKey, ctx: StorageContextType) -> None:
    """Validate complete parent chain (existence + health).

    Combines existence and health checks to ensure all parents exist
    and have well-formed data.

    Args:
        path: Path to validate parents for
        ctx: Storage context (transaction or snapshot)

    Raises:
        PathNotFoundError: If any parent containers are missing
        PathTypeError: If any parent containers have malformed data

    Example:
        >>> validate_parents_chain(("users", "alice", "profile"), tx)
    """
    if not isinstance(ctx, ReadAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement read access protocol. "
            "Use Snapshot or Transaction to read data from storage."
        )

    parent_info = gather_parent_info(path, ctx)

    if not parent_info.all_exist:
        raise PathNotFoundError(f"Missing parent containers: {parent_info.missing_paths}")

    if not parent_info.all_healthy:
        raise PathTypeError(f"Malformed parent containers: {parent_info.malformed_paths}")


def validate_compatible(
    path: TupleKey,
    expected_structure: ContainerStructure,
    expected_protocol: ContainerProtocol,
    ctx: StorageContextType,
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

    Raises:
        PathNotFoundError: If container doesn't exist
        PathTypeError: If type mismatch or malformed data

    Example:
        >>> validate_compatible(
        ...     ("users",), ContainerStructure(1), ContainerProtocol.MUTABLE, tx
        ... )
    """
    if not isinstance(ctx, ReadAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement read access protocol. "
            "Use Snapshot or Transaction to read data from storage."
        )

    info = get_node_info(path, ctx)

    if not info.exists:
        raise PathNotFoundError(f"Container does not exist: {path}")

    if info.node_type != NodeType.CONTAINER:
        raise PathTypeError(f"Path is not a container: {path}")

    if info.structure is None or info.protocol is None:
        raise PathTypeError(f"Container has malformed data: {path}")

    # Structure must match exactly
    if info.structure != expected_structure:
        raise PathTypeError(
            f"Structure mismatch at {path}: expected {expected_structure}, got {info.structure}"
        )

    # Protocol must have at least one common flag
    if not (expected_protocol & info.protocol):
        raise PathTypeError(
            f"Protocol mismatch at {path}: expected {expected_protocol}, got {info.protocol}"
        )
