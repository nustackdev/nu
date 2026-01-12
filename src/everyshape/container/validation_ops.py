"""Validation layer for container operations.

This module enforces container rules and constraints, providing both information
gathering and validation functions. Information functions gather data without
making validation decisions, while validation functions check conditions and
raise exceptions on failure.
"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from .exceptions import ContainerExistsError, ContainerNotFoundError, ContainerTypeError
from .node_ops import gather_parent_info, get_node_info, get_node_type
from .types import ContainerProtocol, ContainerStructure, NodeInfo, NodeType, ParentChainInfo


if TYPE_CHECKING:
    from everyshape.loc import site as site_
    from everyshape.storage import StorageContextType

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
    site: site_.Site, ctx: StorageContextType, *, node_type: NodeType | None = None
) -> None:
    """Validate that node exists at site.

    Args:
        site: Site to validate
        ctx: Storage context (transaction or snapshot)
        node_type: Prefetched node type (optional)

    Raises:
        ContainerNotFoundError: If node does not exist
    """
    node_type = get_node_type(site, ctx) if node_type is None else node_type
    if node_type == NodeType.NOT_FOUND:
        logger.warning("Validation failed: site does not exist", extra={"site": site})
        raise ContainerNotFoundError(f"Site does not exist: {site}")


def validate_not_exists(
    site: site_.Site, ctx: StorageContextType, *, node_type: NodeType | None = None
) -> None:
    """Validate that node does not exist at site.

    Args:
        site: Site to validate
        ctx: Storage context (transaction or snapshot)
        node_type: Prefetched node type (optional)

    Raises:
        ContainerExistsError: If node already exists
    """
    node_type = get_node_type(site, ctx) if node_type is None else node_type
    if node_type != NodeType.NOT_FOUND:
        logger.warning(
            "Validation failed: site already exists",
            extra={"site": site, "node_type": node_type.name},
        )
        raise ContainerExistsError(f"Site already exists: {site}")


def validate_is_container(
    site: site_.Site, ctx: StorageContextType, *, node_type: NodeType | None = None
) -> None:
    """Validate that site is a container.

    Args:
        site: Site to validate
        ctx: Storage context (transaction or snapshot)
        node_type: Prefetched node type (optional)

    Raises:
        ContainerNotFoundError: If site does not exist
        ContainerTypeError: If site is not a container
    """
    node_type = get_node_type(site, ctx) if node_type is None else node_type
    if node_type == NodeType.NOT_FOUND:
        logger.warning("Validation failed: site does not exist", extra={"site": site})
        raise ContainerNotFoundError(f"Site does not exist: {site}")
    if node_type != NodeType.CONTAINER:
        logger.warning(
            "Validation failed: site is not a container",
            extra={"site": site, "actual_type": node_type.name},
        )
        raise ContainerTypeError(f"Site is not a container: {site}")


def validate_is_primitive(
    site: site_.Site, ctx: StorageContextType, *, node_type: NodeType | None = None
) -> None:
    """Validate that site is a primitive value.

    Args:
        site: Site to validate
        ctx: Storage context (transaction or snapshot)
        node_type: Prefetched node type (optional)

    Raises:
        ContainerNotFoundError: If site does not exist
        ContainerTypeError: If site is not a primitive
    """
    node_type = get_node_type(site, ctx) if node_type is None else node_type
    if node_type == NodeType.NOT_FOUND:
        logger.warning("Validation failed: site does not exist", extra={"site": site})
        raise ContainerNotFoundError(f"Site does not exist: {site}")
    if node_type != NodeType.PRIMITIVE:
        logger.warning(
            "Validation failed: site is not a primitive",
            extra={"site": site, "actual_type": node_type.name},
        )
        raise ContainerTypeError(f"Site is not a primitive: {site}")


def validate_parents_exist(
    site: site_.Site, ctx: StorageContextType, *, parent_info: ParentChainInfo | None = None
) -> None:
    """Validate that all parent containers exist.

    Args:
        site: Site to validate parents for
        ctx: Storage context (transaction or snapshot)
        parent_info: Prefetched parent chain info (optional)

    Raises:
        ContainerNotFoundError: If any parent containers are missing
    """
    parent_info = gather_parent_info(site, ctx) if parent_info is None else parent_info
    if not parent_info.all_exist:
        logger.warning(
            "Validation failed: missing parent containers",
            extra={"site": site, "missing_sites": parent_info.missing_sites},
        )
        raise ContainerNotFoundError(f"Missing parent containers: {parent_info.missing_sites}")


def validate_parents_healthy(
    site: site_.Site, ctx: StorageContextType, *, parent_info: ParentChainInfo | None = None
) -> None:
    """Validate that all parent containers have well-formed markers.

    Args:
        site: Site to validate parents for
        ctx: Storage context (transaction or snapshot)
        parent_info: Prefetched parent chain info (optional)

    Raises:
        ContainerTypeError: If any parent containers have malformed data
    """
    parent_info = gather_parent_info(site, ctx) if parent_info is None else parent_info
    if not parent_info.all_healthy:
        logger.error(
            "Validation failed: malformed parent containers",
            extra={"site": site, "malformed_sites": parent_info.malformed_sites},
        )
        raise ContainerTypeError(f"Malformed parent containers: {parent_info.malformed_sites}")


def validate_parents_chain(
    site: site_.Site, ctx: StorageContextType, *, parent_info: ParentChainInfo | None = None
) -> None:
    """Validate complete parent chain (existence + health).

    Combines existence and health checks to ensure all parents exist
    and have well-formed data.

    Args:
        site: Site to validate parents for
        ctx: Storage context (transaction or snapshot)
        parent_info: Prefetched parent chain info (optional)

    Raises:
        ContainerNotFoundError: If any parent containers are missing
        ContainerTypeError: If any parent containers have malformed data
    """
    parent_info = gather_parent_info(site, ctx) if parent_info is None else parent_info

    if not parent_info.all_exist:
        logger.warning(
            "Validation failed: parent chain broken, missing containers",
            extra={"site": site, "missing_sites": parent_info.missing_sites},
        )
        raise ContainerNotFoundError(f"Missing parent containers: {parent_info.missing_sites}")

    if not parent_info.all_healthy:
        logger.error(
            "Validation failed: parent chain broken, malformed containers",
            extra={"site": site, "malformed_sites": parent_info.malformed_sites},
        )
        raise ContainerTypeError(f"Malformed parent containers: {parent_info.malformed_sites}")


def validate_compatible(
    site: site_.Site,
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
        site: Container site to validate
        expected_structure: Required structure ID
        expected_protocol: Required protocol flags (bitwise match)
        ctx: Storage context (transaction or snapshot)
        node_info: Prefetched node info (optional)

    Raises:
        ContainerNotFoundError: If container doesn't exist
        ContainerTypeError: If type mismatch or malformed data
    """
    node_info = get_node_info(site, ctx) if node_info is None else node_info

    if not node_info.exists:
        logger.warning("Validation failed: container does not exist", extra={"site": site})
        raise ContainerNotFoundError(f"Container does not exist: {site}")

    if node_info.node_type != NodeType.CONTAINER:
        logger.warning(
            "Validation failed: site is not a container",
            extra={"site": site, "actual_type": node_info.node_type.name},
        )
        raise ContainerTypeError(f"Site is not a container: {site}")

    if node_info.structure is None or node_info.protocol is None:
        logger.error(
            "Validation failed: container has malformed data",
            extra={"site": site, "structure": node_info.structure, "protocol": node_info.protocol},
        )
        raise ContainerTypeError(f"Container has malformed data: {site}")

    # Structure must match exactly
    if node_info.structure != expected_structure:
        logger.warning(
            "Validation failed: structure mismatch",
            extra={
                "site": site,
                "expected_structure": expected_structure,
                "actual_structure": node_info.structure,
            },
        )
        raise ContainerTypeError(
            f"Structure mismatch at {site}: expected {expected_structure}, got {node_info.structure}"
        )

    # Protocol must have at least one common flag
    if not (expected_protocol & node_info.protocol):
        logger.warning(
            "Validation failed: protocol mismatch",
            extra={
                "site": site,
                "expected_protocol": expected_protocol,
                "actual_protocol": node_info.protocol,
            },
        )
        raise ContainerTypeError(
            f"Protocol mismatch at {site}: expected {expected_protocol}, got {node_info.protocol}"
        )
