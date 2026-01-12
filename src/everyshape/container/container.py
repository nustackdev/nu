"""Container interface for container operations.

This module provides the Container class, a high-level interface for working
with container nodes. Container provides ergonomic access to container
operations while maintaining safety guarantees.

Design principles:
- Stateless: No cached data, always queries storage for accuracy
- Immutable: Pure data structure (NamedTuple) for thread safety
- Explicit context: Context passed at creation, operations use it
- Symmetric: Consistent interface for all child types
- Safe: All operations validate parent existence and type compatibility
- Silent: All mutations return None and are idempotent
"""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from everyshape.loc import DATA_ROOT

from . import container_ops, meta_ops, node_ops, validation_ops
from .exceptions import ContainerInvalidSiteError
from .types import DEFAULT_PARENT_PROTOCOL, DEFAULT_PARENT_STRUCTURE


if TYPE_CHECKING:
    from collections.abc import Generator

    from everyshape.loc import site as site_
    from everyshape.storage import StorageContextType, Subscription, SubscriptionOptions
    from everyshape.types import Empty, Value

    from .types import ContainerProtocol, ContainerStructure, NodeInfo, NodeType, ParentChainInfo

__all__ = [
    "Container",
]


class Container(NamedTuple):
    """Container node interface for container operations.

    A Container represents a single container node and provides operations
    scoped to that container:
    - Self: introspection (info, type, existence)
    - Children: full CRUD operations on direct children
    - Descendants: read-only recursive operations

    This class is stateless - it stores only the site and context, querying
    storage for all data. This ensures operations always reflect current
    storage state, preventing stale data bugs.

    Attributes:
        ctx: Storage context (transaction, snapshot or write batch)
        site: Site of this container

    Safety guarantees:
        - All child operations validate parent existence
        - Type safety: can't replace containers with primitives
        - No stale data: always queries storage
        - Parent chain validation on creation

    All mutations are silent (return None) and idempotent.
    """

    ctx: StorageContextType
    """Storage context (transaction, snapshot, write batch)."""

    site: site_.Site
    """Site of this container."""

    # ========================================================================
    # FACTORY: CONTAINER LIFECYCLE
    # ========================================================================

    @classmethod
    def create(
        cls,
        site: site_.Site,
        ctx: StorageContextType,
        structure: ContainerStructure,
        protocol: ContainerProtocol,
        *,
        default_parent_structure: ContainerStructure = DEFAULT_PARENT_STRUCTURE,
        default_parent_protocol: ContainerProtocol = DEFAULT_PARENT_PROTOCOL,
        ensure_healthy_parents: bool = True,
    ) -> Container:
        """Create new container at site and return Container instance.

        Creates a container in storage and returns a Container instance
        pointing to it. By default, automatically creates any missing
        parent containers.

        Idempotent: silent if container already exists with compatible type.

        Args:
            site: Location for new container
            ctx: Storage context (must support writes)
            structure: Container structure ID (for View reconstruction)
            protocol: Container protocol flags (behavior hints)
            default_parent_structure: Container structure for parent containers
            default_parent_protocol: Container protocol for parent containers
            ensure_healthy_parents: Validate parents chain, create non-existent parents

        Returns:
            Container instance pointing to the container

        Raises:
            ContainerExistsError: If container exists with incompatible type
            ContainerNotFoundError: If ensure_healthy_parents=False and parents missing
            ContainerParentMalformedError: If parent chain has corrupted data
            StorageInterfaceError: If context doesn't support writes
        """
        if not site or site[0] != DATA_ROOT:
            raise ContainerInvalidSiteError(
                "Site is either empty or it doesn't start with ROOT segment"
            )

        container_ops.create_container(
            site,
            structure,
            protocol,
            ctx,
            default_parent_structure=default_parent_structure,
            default_parent_protocol=default_parent_protocol,
            ensure_healthy_parents=ensure_healthy_parents,
        )

        return cls(ctx=ctx, site=site)

    @classmethod
    def get(cls, site: site_.Site, ctx: StorageContextType) -> Container:
        """Get Container instance for existing container.

        Validates that a container exists at the given site and returns
        a Container instance for it. Does not create anything.

        Args:
            site: Container site
            ctx: Storage context

        Returns:
            Container instance

        Raises:
            ContainerNotFoundError: If container doesn't exist
            ContainerTypeError: If site exists but isn't a container
        """
        if not site or site[0] != DATA_ROOT:
            raise ContainerInvalidSiteError(
                "Site is either empty or it doesn't start with ROOT segment"
            )

        validation_ops.validate_is_container(site, ctx)
        return cls(ctx=ctx, site=site)

    # ========================================================================
    # SELF: INTROSPECTION (Read-only)
    # ========================================================================

    def info(self) -> NodeInfo:
        """Get complete node information.

        Fetches current node information from storage, including structure,
        protocol, and other metadata. Always reflects current storage state.

        Returns:
            NodeInfo with current container state

        Raises:
            ContainerNotFoundError: If container doesn't exist
            StorageInterfaceError: If context doesn't support reads
        """
        return node_ops.get_node_info(self.site, self.ctx)

    def exists(self) -> bool:
        """Check if container exists in storage.

        Queries storage to check current existence. Always accurate.

        Returns:
            True if container exists
        """
        return node_ops.node_exists(self.site, self.ctx)

    def node_type(self) -> NodeType:
        """Get node type (should always be CONTAINER).

        Returns:
            NodeType.CONTAINER if container exists

        Raises:
            ContainerNotFoundError: If container doesn't exist
        """
        return node_ops.get_node_type(self.site, self.ctx)

    def parent_chain_info(self) -> ParentChainInfo:
        """Get parent chain health information.

        Gathers information about all parents from root to immediate parent,
        including existence and health status.

        Returns:
            ParentChainInfo with parent health status
        """
        return node_ops.gather_parent_info(self.site, self.ctx)

    # ========================================================================
    # CHILDREN: QUERY (Read operations)
    # ========================================================================

    def exists_child(self, key: site_.SiteSegment) -> bool:
        """Check if direct child exists.

        Args:
            key: Child key to check

        Returns:
            True if child exists

        Raises:
            ContainerNotFoundError: If this container doesn't exist
            StorageInterfaceError: If context doesn't support reads
        """
        return container_ops.exists_child(self.site, key, self.ctx)

    def get_child_type(self, key: site_.SiteSegment) -> NodeType:
        """Get child node type.

        Args:
            key: Child key

        Returns:
            NodeType (CONTAINER, PRIMITIVE, or NOT_FOUND)

        Raises:
            ContainerNotFoundError: If this container doesn't exist
            StorageInterfaceError: If context doesn't support reads
        """
        return container_ops.get_child_type(self.site, key, self.ctx)

    def iter_child_keys(self) -> Generator[site_.SiteSegment, None, None]:
        """Iterate over direct child keys.

        Yields:
            Child keys

        Raises:
            ContainerNotFoundError: If this container doesn't exist
            ContainerTypeError: If site is not a container
            StorageInterfaceError: If context doesn't support reads
        """
        yield from container_ops.iter_child_keys(self.site, self.ctx)

    def iter_children(self) -> Generator[tuple[site_.SiteSegment, NodeInfo], None, None]:
        """Iterate over direct children with their info.

        Yields:
            Tuples of (child_key, NodeInfo)

        Raises:
            ContainerNotFoundError: If this container doesn't exist
            ContainerTypeError: If site is not a container
            StorageInterfaceError: If context doesn't support reads
        """
        yield from container_ops.iter_children(self.site, self.ctx)

    def count_children(self) -> int:
        """Count direct children.

        Returns:
            Number of direct children

        Raises:
            ContainerNotFoundError: If this container doesn't exist
            ContainerTypeError: If site is not a container
            StorageInterfaceError: If context doesn't support reads
        """
        return container_ops.count_children(self.site, self.ctx)

    # ========================================================================
    # CHILDREN: CREATE (Write operations)
    # ========================================================================

    def create_child_container(
        self,
        key: site_.SiteSegment,
        structure: ContainerStructure,
        protocol: ContainerProtocol,
    ) -> Container:
        """Create child container and return Container for it.

        Creates a new container child and returns a Container instance
        pointing to it.

        Idempotent: silent if child container already exists with compatible type.

        Args:
            key: Child key
            structure: Container structure ID
            protocol: Container protocol flags

        Returns:
            Container instance for the child

        Raises:
            ContainerExistsError: If child exists with incompatible type
            ContainerNotFoundError: If this container doesn't exist
            ContainerTypeError: If this is not a container
            StorageInterfaceError: If context doesn't support writes
        """
        container_ops.create_child_container(
            self.site,
            key,
            structure,
            protocol,
            self.ctx,
        )

        child_site = (*self.site, key)
        return Container(ctx=self.ctx, site=child_site)

    def put_child_primitive(
        self,
        key: site_.SiteSegment,
        value: Value,
    ) -> None:
        """Put primitive child value.

        Creates or updates a primitive child. If child exists as a
        container, raises ContainerTypeError.

        Idempotent: overwrites if already exists.

        Args:
            key: Child key
            value: Primitive value to store

        Raises:
            ContainerNotFoundError: If this container doesn't exist
            ContainerTypeError: If this is not a container, or if child exists as a container
            StorageInterfaceError: If context doesn't support writes
        """
        container_ops.put_child_primitive(self.site, key, value, self.ctx)

    def get_child_primitive(self, key: site_.SiteSegment) -> Value | Empty:
        """Get primitive child value.

        Args:
            key: Child key

        Returns:
            Primitive value or EMPTY if doesn't exist

        Raises:
            ContainerNotFoundError: If this container doesn't exist
            ContainerTypeError: If this is not a container, or if child is a container
            StorageInterfaceError: If context doesn't support reads
        """
        return container_ops.get_child_primitive(self.site, key, self.ctx)

    # ========================================================================
    # CHILDREN: DELETE (Write operations)
    # ========================================================================

    def delete_child(
        self,
        key: site_.SiteSegment,
    ) -> None:
        """Delete direct child.

        Idempotent: silent if child doesn't exist.
        If child is a container, deletes all its descendants too.

        Args:
            key: Child key

        Raises:
            ContainerNotFoundError: If this container doesn't exist
            StorageInterfaceError: If context doesn't support writes
        """
        container_ops.delete_child(self.site, key, self.ctx)

    def clear_children(self) -> None:
        """Delete all direct children.

        Removes all children of this container. Container children are
        deleted recursively.

        Idempotent: silent if no children exist.

        Raises:
            ContainerNotFoundError: If this container doesn't exist
            ContainerTypeError: If this is not a container
            StorageInterfaceError: If context doesn't support writes
        """
        container_ops.clear_children(self.site, self.ctx)

    # ========================================================================
    # DESCENDANTS: RECURSIVE READ-ONLY OPERATIONS
    # ========================================================================

    def iter_descendants(
        self,
        *,
        depth: int = -1,
    ) -> Generator[site_.Site, None, None]:
        """Iterate over all descendants.

        Args:
            depth: Depth to traverse (-1=unlimited, 1=children, >1 exact depth match)

        Yields:
            Descendant sites

        Raises:
            ContainerNotFoundError: If this container doesn't exist
            ContainerTypeError: If this is not a container
            StorageInterfaceError: If context doesn't support reads
            ContainerInvalidDepthError: If depth argument is invalid
        """
        yield from container_ops.iter_descendants(self.site, self.ctx, depth=depth)

    def walk_descendants(self) -> Generator[tuple[site_.Site, NodeType], None, None]:
        """Walk over descendant structure.

        Yields:
            Tuples of (site, NodeType) for each descendant

        Raises:
            ContainerNotFoundError: If this container doesn't exist
            ContainerTypeError: If this is not a container
            StorageInterfaceError: If context doesn't support reads
        """
        return container_ops.walk_descendants(self.site, self.ctx)

    # ========================================================================
    # SELF: DESTRUCTIVE OPERATIONS
    # ========================================================================

    def delete(self) -> None:
        """Delete this container and all descendants.

        Idempotent: silent if container doesn't exist.

        Raises:
            ContainerTypeError: If site exists but is not a container
            StorageInterfaceError: If context doesn't support writes

        Warning:
            After deletion, this Container instance becomes invalid.
            Further operations will raise ContainerNotFoundError.
        """
        container_ops.delete_container(self.site, self.ctx)

    # ========================================================================
    # VALIDATION HELPERS
    # ========================================================================

    def validate_compatible(
        self,
        structure: ContainerStructure,
        protocol: ContainerProtocol,
    ) -> None:
        """Validate container matches expected type.

        Checks that this container has the expected structure and protocol.
        Useful when you need to ensure a container is of a specific type.

        Args:
            structure: Expected structure ID
            protocol: Expected protocol flags (bitwise match)

        Raises:
            ContainerNotFoundError: If container doesn't exist
            ContainerTypeError: If type mismatch or malformed data
        """
        validation_ops.validate_compatible(
            self.site,
            structure,
            protocol,
            self.ctx,
        )

    # ========================================================================
    # METADATA: FLAT KEY-VALUE STORAGE AT /m TREE
    # ========================================================================

    def put_metadata(self, key: site_.SiteSegment, value: Value) -> None:
        """Put metadata for this container.

        Metadata is stored in the /m tree parallel to the data tree.
        Metadata must be primitive values (no containers).

        Idempotent: overwrites if already exists.

        Args:
            key: Metadata key
            value: Primitive value to store

        Raises:
            ContainerNotFoundError: If this container doesn't exist
            StorageInterfaceError: If context doesn't support writes
        """
        meta_ops.put_metadata(self.site, key, value, self.ctx)

    def get_metadata(self, key: site_.SiteSegment, default: Value | Empty = None) -> Value | Empty:
        """Get metadata value.

        Args:
            key: Metadata key
            default: Default value if not found (defaults to None)

        Returns:
            Metadata value or default if doesn't exist

        Raises:
            ContainerNotFoundError: If this container doesn't exist
            StorageInterfaceError: If context doesn't support reads
        """
        return meta_ops.get_metadata(self.site, key, self.ctx, default)

    def exists_metadata(self, key: site_.SiteSegment) -> bool:
        """Check if metadata key exists.

        Args:
            key: Metadata key to check

        Returns:
            True if metadata exists

        Raises:
            ContainerNotFoundError: If this container doesn't exist
            StorageInterfaceError: If context doesn't support reads
        """
        return meta_ops.exists_metadata(self.site, key, self.ctx)

    def delete_metadata(self, key: site_.SiteSegment) -> None:
        """Delete metadata key.

        Idempotent: silent if metadata doesn't exist.

        Args:
            key: Metadata key to delete

        Raises:
            ContainerNotFoundError: If this container doesn't exist
            StorageInterfaceError: If context doesn't support writes
        """
        meta_ops.delete_metadata(self.site, key, self.ctx)

    def iter_metadata_keys(self) -> Generator[site_.SiteSegment, None, None]:
        """Iterate over metadata keys for this container.

        Yields:
            Metadata keys

        Raises:
            ContainerNotFoundError: If this container doesn't exist
            StorageInterfaceError: If context doesn't support reads
        """
        yield from meta_ops.iter_metadata_keys(self.site, self.ctx)

    # ========================================================================
    # SUBSCRIPTIONS: CONTAINER CHANGES
    # ========================================================================

    def subscribe(self, options: SubscriptionOptions) -> Subscription:
        """Subscribe to key changes with flexible filtering.

        Args:
            options: Subscription options including filter specification

        Returns:
            Subscription object for binding callbacks and managing lifecycle.

        Raises:
            StorageOperationError: If subscription fails or observer not configured.
        """
        return self.ctx.storage.subscribe(options)

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def get_child_container(self, key: site_.SiteSegment) -> Container:
        """Get Container instance for child container.

        Convenience method that combines validation and Container creation.

        Args:
            key: Child key

        Returns:
            Container instance for child

        Raises:
            ContainerNotFoundError: If this container or child doesn't exist
            ContainerTypeError: If child is not a container
        """
        child_site = (*self.site, key)
        validation_ops.validate_is_container(child_site, self.ctx)
        return Container(ctx=self.ctx, site=child_site)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<Container(site={self.site})>"

    def __str__(self) -> str:
        """Human-readable string."""
        return f"Container at {self.site}"
