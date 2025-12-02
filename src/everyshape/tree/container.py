"""Container interface for tree operations.

This module provides the Container class, a high-level interface for working
with container nodes in the tree. Container provides ergonomic access to
container operations while maintaining safety guarantees.

Design principles:
- Stateless: No cached data, always queries storage for accuracy
- Immutable: Pure data structure (NamedTuple) for thread safety
- Explicit context: Context passed at creation, operations use it
- Symmetric: Consistent interface for all child types
- Safe: All operations validate parent existence and type compatibility

Example:
    >>> from everyshape.tree import Container, ContainerStructure, ContainerProtocol
    >>> with storage.transaction() as tx:
    ...     # Create root container
    ...     root = Container.create(
    ...         path=(),
    ...         ctx=tx,
    ...         structure=ContainerStructure(1),
    ...         protocol=ContainerProtocol.MUTABLE,
    ...     )
    ...
    ...     # Create child containers
    ...     users = root.create_child_container(
    ...         "users",
    ...         ContainerStructure(1),
    ...         ContainerProtocol.MUTABLE,
    ...     )
    ...
    ...     # Add primitive children
    ...     users.set_child_primitive("alice", {"name": "Alice", "age": 30})
    ...     users.set_child_primitive("bob", {"name": "Bob", "age": 25})
    ...
    ...     # Query operations
    ...     info = users.info()
    ...     print(f"Container: {info.path}")
    ...     print(f"Children: {users.list_child_keys()}")
    ...
    ...     # Navigate
    ...     alice_data = users.get_child_primitive("alice")
    ...     print(f"Alice: {alice_data}")
"""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from everyshape.loc import key as key_

from . import container_ops, meta_ops, node_ops, validation_ops
from .exceptions import InvalidPathError
from .types import DEFAULT_PARENT_PROTOCOL, DEFAULT_PARENT_STRUCTURE


if TYPE_CHECKING:
    from collections.abc import Generator

    from everyshape.storage import (
        CallbackFn,
        StorageContextType,
        StorageProtocol,
        SubscriptionProtocol,
    )
    from everyshape.types import Empty, Value

    from .types import (
        ContainerProtocol,
        ContainerStructure,
        NodeInfo,
        NodeType,
        ParentChainInfo,
    )

__all__ = [
    "Container",
]


class Container(NamedTuple):
    """Container node interface for tree operations.

    A Container represents a single container node in the tree and provides
    operations scoped to that container:
    - Self: introspection (info, type, existence)
    - Children: full CRUD operations on direct children
    - Descendants: read-only recursive operations

    This class is stateless - it stores only the path and context, querying
    storage for all data. This ensures operations always reflect current
    storage state, preventing stale data bugs.

    Attributes:
        ctx: Storage context (transaction or snapshot)
        path: Path to this container in the tree

    Safety guarantees:
        - All child operations validate parent existence
        - Type safety: can't replace containers with primitives
        - No stale data: always queries storage
        - Parent chain validation on creation

    Example:
        >>> with storage.transaction() as tx:
        ...     container = Container.create(("users",), tx, structure, protocol)
        ...     container.set_child_primitive("alice", {"name": "Alice"})
        ...     children = container.list_child_keys()
    """

    ctx: StorageContextType
    """Storage context (transaction or snapshot)."""

    path: key_.Key
    """Path to this container in the tree."""

    # ========================================================================
    # FACTORY: CONTAINER LIFECYCLE
    # ========================================================================

    @classmethod
    def create(
        cls,
        path: key_.Key,
        ctx: StorageContextType,
        structure: ContainerStructure,
        protocol: ContainerProtocol,
        *,
        default_parent_structure: ContainerStructure = DEFAULT_PARENT_STRUCTURE,
        default_parent_protocol: ContainerProtocol = DEFAULT_PARENT_PROTOCOL,
        ensure_healthy_parents: bool = True,
    ) -> Container:
        """Create new container at path and return Container instance.

        Creates a container in storage and returns a Container instance
        pointing to it. By default, automatically creates any missing
        parent containers.

        Args:
            path: Location for new container
            ctx: Storage context (must support writes)
            structure: Container structure ID (for View reconstruction)
            protocol: Container protocol flags (behavior hints)
            default_parent_structure: Container structure for parent containers
            default_parent_protocol: Container protocol for parent containers
            ensure_healthy_parents: Validate parents chain, create non-existent parents

        Returns:
            Container instance pointing to newly created container

        Raises:
            PathExistsError: If container already exists at path
            PathNotFoundError: If create_parents=False and parents missing
            ParentMalformedError: If parent chain has corrupted data
            StorageInterfaceError: If context doesn't support writes

        Example:
            >>> container = Container.create(
            ...     ("users", "alice"),
            ...     tx,
            ...     ContainerStructure(1),
            ...     ContainerProtocol.MUTABLE,
            ... )
        """
        if not path or path[0] != key_.DATA_ROOT:
            raise InvalidPathError("Path is either empty or it doesn't start with ROOT segment")

        container_ops.create_container(
            path,
            structure,
            protocol,
            ctx,
            default_parent_structure=default_parent_structure,
            default_parent_protocol=default_parent_protocol,
            ensure_healthy_parents=ensure_healthy_parents,
        )

        return cls(ctx=ctx, path=path)

    @classmethod
    def get(cls, path: key_.Key, ctx: StorageContextType) -> Container:
        """Get Container instance for existing container.

        Validates that a container exists at the given path and returns
        a Container instance for it. Does not create anything.

        Args:
            path: Container path
            ctx: Storage context

        Returns:
            Container instance

        Raises:
            PathNotFoundError: If container doesn't exist
            PathTypeError: If path exists but isn't a container

        Example:
            >>> container = Container.get(("users", "alice"), tx)
            >>> info = container.info()
        """
        if not path or path[0] != key_.DATA_ROOT:
            raise InvalidPathError("Path is either empty or it doesn't start with ROOT segment")

        validation_ops.validate_is_container(path, ctx)
        return cls(ctx=ctx, path=path)

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
            PathNotFoundError: If container doesn't exist
            StorageInterfaceError: If context doesn't support reads

        Example:
            >>> info = container.info()
            >>> print(f"Structure: {info.structure}")
            >>> print(f"Protocol: {info.protocol}")
        """
        return node_ops.get_node_info(self.path, self.ctx)

    def exists(self) -> bool:
        """Check if container exists in storage.

        Queries storage to check current existence. Always accurate.

        Returns:
            True if container exists

        Example:
            >>> if container.exists():
            ...     print("Container is present")
        """
        return node_ops.node_exists(self.path, self.ctx)

    def node_type(self) -> NodeType:
        """Get node type (should always be CONTAINER).

        Returns:
            NodeType.CONTAINER if container exists

        Raises:
            PathNotFoundError: If container doesn't exist

        Example:
            >>> node_type = container.node_type()
            >>> assert node_type == NodeType.CONTAINER
        """
        return node_ops.get_node_type(self.path, self.ctx)

    def parent_chain_info(self) -> ParentChainInfo:
        """Get parent chain health information.

        Gathers information about all parents from root to immediate parent,
        including existence and health status.

        Returns:
            ParentChainInfo with parent health status

        Example:
            >>> chain_info = container.parent_chain_info()
            >>> if chain_info.all_exist and chain_info.all_healthy:
            ...     print("Parent chain is healthy")
        """
        return node_ops.gather_parent_info(self.path, self.ctx)

    # ========================================================================
    # CHILDREN: QUERY (Read operations)
    # ========================================================================

    def has_child(self, key: key_.KeySegment) -> bool:
        """Check if direct child exists.

        Args:
            key: Child key to check

        Returns:
            True if child exists

        Raises:
            PathNotFoundError: If this container doesn't exist
            StorageInterfaceError: If context doesn't support reads

        Example:
            >>> if container.has_child("alice"):
            ...     print("Alice exists")
        """
        return container_ops.has_child(self.path, key, self.ctx)

    def get_child_type(self, key: key_.KeySegment) -> NodeType:
        """Get child node type.

        Args:
            key: Child key

        Returns:
            NodeType (CONTAINER, PRIMITIVE, or NOT_FOUND)

        Raises:
            PathNotFoundError: If this container doesn't exist
            StorageInterfaceError: If context doesn't support reads

        Example:
            >>> child_type = container.get_child_type("alice")
            >>> if child_type == NodeType.PRIMITIVE:
            ...     print("Alice is a primitive value")
        """
        return container_ops.get_child_type(self.path, key, self.ctx)

    def list_child_keys(self) -> Generator[key_.KeySegment, None, None]:
        """List direct child keys.

        Returns:
            List of child keys (unsorted)

        Raises:
            PathNotFoundError: If this container doesn't exist
            PathTypeError: If path is not a container
            StorageInterfaceError: If context doesn't support reads

        Example:
            >>> keys = container.list_child_keys()
            >>> print(f"Children: {keys}")
        """
        yield from container_ops.list_child_keys(self.path, self.ctx)

    def list_children(self) -> Generator[tuple[key_.KeySegment, NodeInfo], None, None]:
        """List direct child paths.

        Returns full paths for all direct children.

        Returns:
            List of full child paths

        Raises:
            PathNotFoundError: If this container doesn't exist
            PathTypeError: If path is not a container
            StorageInterfaceError: If context doesn't support reads

        Example:
            >>> children = container.list_children()
            >>> for child_path in children:
            ...     print(f"Child: {child_path}")
        """
        yield from container_ops.list_children(self.path, self.ctx)

    def count_children(self) -> int:
        """Count direct children.

        Returns:
            Number of direct children

        Raises:
            PathNotFoundError: If this container doesn't exist
            PathTypeError: If path is not a container
            StorageInterfaceError: If context doesn't support reads

        Example:
            >>> count = container.count_children()
            >>> print(f"Container has {count} children")
        """
        return container_ops.count_children(self.path, self.ctx)

    # ========================================================================
    # CHILDREN: CREATE (Write operations)
    # ========================================================================

    def create_child_container(
        self,
        key: key_.KeySegment,
        structure: ContainerStructure,
        protocol: ContainerProtocol,
    ) -> Container:
        """Create child container and return Container for it.

        Creates a new container child and returns a Container instance
        pointing to it.

        Args:
            key: Child key
            structure: Container structure ID
            protocol: Container protocol flags

        Returns:
            Container instance for new child

        Raises:
            PathExistsError: If child already exists
            PathNotFoundError: If this container doesn't exist
            PathTypeError: If this is not a container
            StorageInterfaceError: If context doesn't support writes

        Example:
            >>> posts = user_container.create_child_container(
            ...     "posts",
            ...     ContainerStructure(2),
            ...     ContainerProtocol.MUTABLE,
            ... )
            >>> posts.set_child_primitive("post1", {"title": "First post"})
        """
        container_ops.create_child_container(
            self.path,
            key,
            structure,
            protocol,
            self.ctx,
        )

        child_path = key_.join_segment(self.path, key)
        return Container(ctx=self.ctx, path=child_path)

    def set_child_primitive(
        self,
        key: key_.KeySegment,
        value: Value,
    ) -> None:
        """Set primitive child value.

        Creates or updates a primitive child. If child exists as a
        container, raises PathTypeError.

        Args:
            key: Child key
            value: Primitive value to store

        Raises:
            PathNotFoundError: If this container doesn't exist
            PathTypeError: If this is not a container, or if child
                exists as a container
            StorageInterfaceError: If context doesn't support writes

        Example:
            >>> container.set_child_primitive("name", "Alice")
            >>> container.set_child_primitive("age", 30)
        """
        container_ops.set_child_primitive(self.path, key, value, self.ctx)

    def get_child_primitive(self, key: key_.KeySegment) -> Value | Empty:
        """Get primitive child value.

        Args:
            key: Child key

        Returns:
            Primitive value or EMPTY if doesn't exist

        Raises:
            PathNotFoundError: If this container doesn't exist
            PathTypeError: If this is not a container, or if child
                is a container
            StorageInterfaceError: If context doesn't support reads

        Example:
            >>> name = container.get_child_primitive("name")
            >>> if not is_empty(name):
            ...     print(f"Name: {name}")
        """
        return container_ops.get_child_primitive(self.path, key, self.ctx)

    # ========================================================================
    # CHILDREN: DELETE (Write operations)
    # ========================================================================

    def delete_child(
        self,
        key: key_.KeySegment,
    ) -> bool:
        """Delete direct child.

        Deletes a child node (both containers and primitives).

        Args:
            key: Child key

        Returns:
            True if deleted, False if didn't exist

        Raises:
            PathNotFoundError: If this container doesn't exist
            StorageInterfaceError: If context doesn't support writes

        Example:
            >>> # Delete primitive child
            >>> container.delete_child("old_field")
            True
            >>>
            >>> # Delete container child and its subtree
            >>> container.delete_child("old_section")
            True
        """
        return container_ops.delete_child(self.path, key, self.ctx)

    def clear_children(self) -> int:
        """Delete all direct children.

        Removes all children of this container. Container children are
        deleted recursively.

        Returns:
            Number of children deleted

        Raises:
            PathNotFoundError: If this container doesn't exist
            PathTypeError: If this is not a container
            StorageInterfaceError: If context doesn't support writes

        Example:
            >>> count = container.clear_children()
            >>> print(f"Deleted {count} children")
        """
        return container_ops.clear_children(self.path, self.ctx)

    # ========================================================================
    # DESCENDANTS: RECURSIVE READ-ONLY OPERATIONS
    # ========================================================================

    def list_descendants(
        self,
        *,
        depth: int = -1,
    ) -> Generator[key_.Key, None, None]:
        """List all descendants recursively.

        Returns all descendant paths, optionally limited by depth.

        Args:
            depth: Depth to traverse (-1=unlimited, 1=children, >1 exact depth match)

        Returns:
            List of descendant paths (full path tuples)

        Raises:
            PathNotFoundError: If this container doesn't exist
            PathTypeError: If this is not a container
            StorageInterfaceError: If context doesn't support reads
            InvalidDepthError: If depth arguments is invalid

        Example:
            >>> # Get all descendants
            >>> all_descendants = container.list_descendants()
            >>>
            >>> # Get only grandchildren
            >>> nearby = container.list_descendants(depth=2)
        """
        yield from container_ops.list_descendants(self.path, self.ctx, depth=depth)

    def walk_tree(self) -> Generator[tuple[key_.Key, NodeType], None, None]:
        """Iterate over tree structure.

        Yields (path, node_type) tuples for all descendants.

        Yields:
            (path, node_type) tuples

        Raises:
            PathNotFoundError: If this container doesn't exist
            PathTypeError: If this is not a container
            StorageInterfaceError: If context doesn't support reads

        Example:
            >>> for child_path, node_type in container.walk_tree():
            ...     if node_type == NodeType.CONTAINER:
            ...         print(f"Container: {child_path}")
            ...     else:
            ...         print(f"Primitive: {child_path}")
        """
        return container_ops.walk_tree(self.path, self.ctx)

    # ========================================================================
    # SELF: DESTRUCTIVE OPERATIONS
    # ========================================================================

    def delete(self) -> bool:
        """Delete this container.

        Deletes this container from storage. Deletes entire subtree.

        Returns:
            True if deleted, False if didn't exist

        Raises:
            StorageInterfaceError: If context doesn't support writes

        Warning:
            After deletion, this Container instance becomes invalid.
            Further operations will raise PathNotFoundError.

        Example:
            >>> container = Container.create(("temp",), tx, ...)
            >>> container.set_child_primitive("data", "value")
            >>> container.delete(recursive=True)
            True
            >>> container.exists()  # False
        """
        return container_ops.delete_container(self.path, self.ctx)

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
            PathNotFoundError: If container doesn't exist
            PathTypeError: If type mismatch or malformed data

        Example:
            >>> # Ensure container is a DictView container
            >>> container.validate_compatible(
            ...     ContainerStructure(1),
            ...     ContainerProtocol.MUTABLE,
            ... )
        """
        validation_ops.validate_compatible(
            self.path,
            structure,
            protocol,
            self.ctx,
        )

    # ========================================================================
    # METADATA: FLAT KEY-VALUE STORAGE AT /m TREE
    # ========================================================================

    def set_metadata(self, key: key_.KeySegment, value: Value) -> None:
        """Set metadata for this container.

        Metadata is stored in the /m tree parallel to the data tree.
        Metadata must be primitive values (no containers).

        Args:
            key: Metadata key
            value: Primitive value to store

        Raises:
            PathNotFoundError: If this container doesn't exist
            StorageInterfaceError: If context doesn't support writes

        Example:
            >>> container.set_metadata("created_at", 1234567890)
            >>> container.set_metadata("version", "1.0")
        """
        meta_ops.set_metadata(self.path, key, value, self.ctx)

    def get_metadata(self, key: key_.KeySegment, default: Value | Empty = None) -> Value | Empty:
        """Get metadata value.

        Args:
            key: Metadata key
            default: Default value if not found (defaults to None)

        Returns:
            Metadata value or default if doesn't exist

        Raises:
            PathNotFoundError: If this container doesn't exist
            StorageInterfaceError: If context doesn't support reads

        Example:
            >>> created = container.get_metadata("created_at")
            >>> if created is not None:
            ...     print(f"Created at: {created}")
        """
        return meta_ops.get_metadata(self.path, key, self.ctx, default)

    def has_metadata(self, key: key_.KeySegment) -> bool:
        """Check if metadata key exists.

        Args:
            key: Metadata key to check

        Returns:
            True if metadata exists

        Raises:
            PathNotFoundError: If this container doesn't exist
            StorageInterfaceError: If context doesn't support reads

        Example:
            >>> if container.has_metadata("version"):
            ...     print("Version metadata exists")
        """
        return meta_ops.has_metadata(self.path, key, self.ctx)

    def delete_metadata(self, key: key_.KeySegment) -> bool:
        """Delete metadata key.

        Args:
            key: Metadata key to delete

        Returns:
            True if deleted, False if didn't exist

        Raises:
            PathNotFoundError: If this container doesn't exist
            StorageInterfaceError: If context doesn't support writes

        Example:
            >>> container.delete_metadata("temp_flag")
            True
        """
        return meta_ops.delete_metadata(self.path, key, self.ctx)

    def list_metadata_keys(self) -> Generator[key_.KeySegment, None, None]:
        """List all metadata keys for this container.

        Returns:
            Generator of metadata keys

        Raises:
            PathNotFoundError: If this container doesn't exist
            StorageInterfaceError: If context doesn't support reads

        Example:
            >>> for key in container.list_metadata_keys():
            ...     value = container.get_metadata(key)
            ...     print(f"{key}: {value}")
        """
        yield from meta_ops.list_metadata_keys(self.path, self.ctx)

    # ========================================================================
    # SUBSCRIPTIONS: WATCH CONTAINER CHANGES
    # ========================================================================

    def watch_child(
        self,
        storage: StorageProtocol,
        key: key_.KeySegment,
        callback: CallbackFn,
        depth: int = -1,
    ) -> SubscriptionProtocol:
        """Watch changes to a specific child and its subtree.

        Args:
            storage: Storage instance for subscriptions
            key: Child key to watch
            callback: Function called on changes
            depth: Subscription depth (-1=entire subtree, 0=exact, N=depth)

        Returns:
            Subscription handle

        Raises:
            StorageOperationError: If subscription fails

        Example:
            >>> sub = container.watch_child(storage, "alice", my_callback)
            >>> # Callback fires on changes to /users/alice/**
        """
        child_path = key_.join_segment(self.path, key)
        return storage.subscribe(child_path, callback, depth)

    def watch_children(
        self,
        storage: StorageProtocol,
        *keys: key_.KeySegment,
        callback: CallbackFn,
        depth: int = -1,
    ) -> tuple[SubscriptionProtocol, ...]:
        """Watch changes to multiple children and their subtrees.

        Args:
            storage: Storage instance for subscriptions
            *keys: Child keys to watch
            callback: Function called on changes
            depth: Subscription depth (-1=entire subtree, 0=exact, N=depth)

        Returns:
            Tuple of subscription handles

        Raises:
            StorageOperationError: If subscription fails

        Example:
            >>> subs = container.watch_children(storage, "alice", "bob", callback=my_callback)
            >>> # subs is (sub1, sub2)
        """
        return tuple(
            storage.subscribe(key_.join_segment(self.path, key), callback, depth) for key in keys
        )

    def watch(
        self,
        storage: StorageProtocol,
        callback: CallbackFn,
        depth: int = -1,
    ) -> SubscriptionProtocol:
        """Watch changes to this container and its descendants.

        Args:
            storage: Storage instance for subscriptions
            callback: Function called on changes
            depth: Subscription depth (-1=entire tree, 0=exact, N=depth)

        Returns:
            Subscription handle

        Raises:
            StorageOperationError: If subscription fails

        Example:
            >>> sub = container.watch(storage, my_callback)
            >>> # Callback fires on any change at or under this container
        """
        return storage.subscribe(self.path, callback, depth)

    def unwatch(
        self,
        storage: StorageProtocol,
        subscription: SubscriptionProtocol,
    ) -> None:
        """Unsubscribe from changes.

        Convenience wrapper for storage.unsubscribe().

        Args:
            storage: Storage instance
            subscription: Subscription to cancel

        Raises:
            StorageOperationError: If unsubscribe fails

        Example:
            >>> sub = container.watch_child(storage, "alice", callback)
            >>> container.unwatch(storage, sub)
        """
        storage.unsubscribe(subscription)

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def get_child_container(self, key: key_.KeySegment) -> Container:
        """Get Container instance for child container.

        Convenience method that combines validation and Container creation.

        Args:
            key: Child key

        Returns:
            Container instance for child

        Raises:
            PathNotFoundError: If this container or child doesn't exist
            PathTypeError: If child is not a container

        Example:
            >>> users = root.get_child_container("users")
            >>> alice = users.get_child_container("alice")
        """
        child_path = key_.join_segment(self.path, key)
        validation_ops.validate_is_container(child_path, self.ctx)
        return Container(ctx=self.ctx, path=child_path)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<Container(path={self.path})>"

    def __str__(self) -> str:
        """Human-readable string."""
        return f"Container at {self.path}"
