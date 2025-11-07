"""Tree interface - main entry point for tree operations.

This module provides the Tree class, a convenience wrapper that binds a storage
context to tree operations. It delegates all operations to the functional API
modules while providing a more ergonomic object-oriented interface.

The Tree class is optional - all operations can be called directly as module
functions with explicit context passing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from redwood.abc import EMPTY
from redwood.be import StorageKeyError
from redwood.utils.path import Path

from . import container_ops as container_ops
from . import navigation as nav
from . import node_ops as node_ops
from . import validation_ops as val_ops
from .types import (
    ContainerProtocol,
    ContainerStructure,
    NodeInfo,
    NodeType,
    ParentChainInfo,
    require_read_context,
    require_write_context,
)


if TYPE_CHECKING:
    from collections.abc import Generator

    from redwood.abc import Empty, KeyComponent, TupleKey, Value
    from redwood.be import StorageContextType

__all__ = [
    "Tree",
]


class Tree(NamedTuple):
    """Tree interface with convenience methods.

    Optional wrapper around functional API that binds a storage context,
    providing an object-oriented interface to tree operations. All methods
    delegate to module-level functions.

    This class is immutable (frozen) for thread safety and caching.

    Attributes:
        ctx: Storage context (transaction or snapshot)

    Example:
        >>> with storage.transaction() as tx:
        ...     tree = Tree(ctx=tx)
        ...     tree.create_container(
        ...         ("users", "alice"), ContainerStructure(1), ContainerProtocol.MUTABLE
        ...     )
        ...     info = tree.get_node_info(("users", "alice"))
    """

    ctx: StorageContextType

    # ========================================================================
    # NODE OPERATIONS
    # ========================================================================

    def get_node_info(self, path: TupleKey) -> NodeInfo:
        """Get complete node information.

        Args:
            path: Node path

        Returns:
            NodeInfo with all available data

        Example:
            >>> info = tree.get_node_info(("users", "alice"))
            >>> if info.node_type == NodeType.CONTAINER:
            ...     print("It's a container")
        """
        return node_ops.get_node_info(path, self.ctx)

    def get_node_type(self, path: TupleKey) -> NodeType:
        """Get node type.

        Args:
            path: Node path

        Returns:
            NodeType (CONTAINER, PRIMITIVE, or NOT_FOUND)

        Example:
            >>> node_type = tree.get_node_type(("users", "alice"))
        """
        return node_ops.get_node_type(path, self.ctx)

    def exists(self, path: TupleKey) -> bool:
        """Check if node exists.

        Args:
            path: Node path

        Returns:
            True if node exists

        Example:
            >>> if tree.exists(("users", "alice")):
            ...     print("User exists")
        """
        return node_ops.node_exists(path, self.ctx)

    # ========================================================================
    # VALIDATION OPERATIONS
    # ========================================================================

    def gather_parent_info(self, path: TupleKey) -> ParentChainInfo:
        """Gather parent chain information.

        Args:
            path: Path to gather parent info for

        Returns:
            ParentChainInfo with parent chain data

        Example:
            >>> info = tree.gather_parent_info(("users", "alice", "profile"))
            >>> if not info.all_exist:
            ...     print(f"Missing parents: {info.missing_paths}")
        """
        return val_ops.gather_parent_info(path, self.ctx)

    def validate_exists(self, path: TupleKey) -> None:
        """Validate node exists (raises if not)."""
        val_ops.validate_exists(path, self.ctx)

    def validate_not_exists(self, path: TupleKey) -> None:
        """Validate node doesn't exist (raises if exists)."""
        val_ops.validate_not_exists(path, self.ctx)

    def validate_is_container(self, path: TupleKey) -> None:
        """Validate path is a container (raises if not)."""
        val_ops.validate_is_container(path, self.ctx)

    def validate_is_primitive(self, path: TupleKey) -> None:
        """Validate path is a primitive (raises if not)."""
        val_ops.validate_is_primitive(path, self.ctx)

    def validate_parents_exist(self, path: TupleKey) -> None:
        """Validate all parents exist (raises if missing)."""
        val_ops.validate_parents_exist(path, self.ctx)

    def validate_parents_healthy(self, path: TupleKey) -> None:
        """Validate all parents are well-formed (raises if malformed)."""
        val_ops.validate_parents_healthy(path, self.ctx)

    def validate_parents_chain(self, path: TupleKey) -> None:
        """Validate complete parent chain (raises if issues)."""
        val_ops.validate_parents_chain(path, self.ctx)

    def validate_compatible(
        self,
        path: TupleKey,
        expected_structure: ContainerStructure,
        expected_protocol: ContainerProtocol,
    ) -> None:
        """Validate container type matches expectations (raises if mismatch)."""
        val_ops.validate_compatible(path, expected_structure, expected_protocol, self.ctx)

    # ========================================================================
    # CONTAINER LIFECYCLE
    # ========================================================================

    def create_container(
        self,
        path: TupleKey,
        structure: ContainerStructure,
        protocol: ContainerProtocol,
        *,
        ensure_healthy_parents: bool = True,
    ) -> bool:
        """Create container at path.

        Args:
            path: Container path
            structure: Container structure ID
            protocol: Container protocol flags
            ensure_healthy_parents: Validate parents chain, create non-existent parents

        Returns:
            True if created, False if already exists with compatible type

        Example:
            >>> tree.create_container(
            ...     ("users", "alice"), ContainerStructure(1), ContainerProtocol.MUTABLE
            ... )
            True
        """
        return container_ops.create_container(
            path, structure, protocol, self.ctx, ensure_healthy_parents=ensure_healthy_parents
        )

    def delete_container(self, path: TupleKey, *, recursive: bool = False) -> bool:
        """Delete container.

        Args:
            path: Container path
            recursive: If True, delete all children

        Returns:
            True if deleted, False if didn't exist

        Example:
            >>> tree.delete_container(("users", "alice"), recursive=True)
            True
        """
        return container_ops.delete_container(path, self.ctx, recursive=recursive)

    def delete_subtree(self, path: TupleKey) -> int:
        """Delete container and all descendants.

        Args:
            path: Container path

        Returns:
            Number of nodes deleted

        Example:
            >>> count = tree.delete_subtree(("users", "alice"))
            >>> print(f"Deleted {count} nodes")
        """
        return container_ops.delete_subtree(path, self.ctx)

    # ========================================================================
    # METADATA OPERATIONS
    # ========================================================================

    def get_metadata(
        self,
        path: TupleKey,
        key: KeyComponent,
        default: Value | Empty = EMPTY,
    ) -> Value | Empty:
        """Get metadata value stored under a container's metadata namespace.

        Args:
            path: Container path
            key: Metadata key (e.g., "__length__")
            default: Value to return if metadata is not found

        Returns:
            Stored metadata value or the provided default if missing
        """
        metadata_path = Path.join(Path.to_meta(path), key)
        ctx = require_read_context(self.ctx)
        try:
            return ctx.get(metadata_path)
        except StorageKeyError:
            return default

    def set_metadata(self, path: TupleKey, key: KeyComponent, value: Value) -> None:
        """Set metadata value under a container's metadata namespace.

        Args:
            path: Container path
            key: Metadata key
            value: Metadata value to store
        """
        metadata_path = Path.join(Path.to_meta(path), key)
        ctx = require_write_context(self.ctx)
        ctx.put(metadata_path, value)

    def has_metadata(self, path: TupleKey, key: KeyComponent) -> bool:
        """Check whether a metadata key exists for a container.

        Args:
            path: Container path
            key: Metadata key

        Returns:
            True if the metadata key exists, False otherwise
        """
        metadata_path = Path.join(Path.to_meta(path), key)
        ctx = require_read_context(self.ctx)
        return ctx.has(metadata_path)

    def delete_metadata(self, path: TupleKey, key: KeyComponent) -> bool:
        """Delete a metadata key for a container.

        Args:
            path: Container path
            key: Metadata key to delete

        Returns:
            True if a metadata entry was deleted, False if it did not exist
        """
        metadata_path = Path.join(Path.to_meta(path), key)
        ctx = require_write_context(self.ctx)
        try:
            return ctx.delete(metadata_path)
        except StorageKeyError:
            return False

    # ========================================================================
    # CHILD OPERATIONS
    # ========================================================================

    def has_child(self, path: TupleKey, key: KeyComponent) -> bool:
        """Check if direct child exists.

        Args:
            path: Container path
            key: Child key

        Returns:
            True if child exists

        Example:
            >>> if tree.has_child(("users", "alice"), "profile"):
            ...     print("Profile exists")
        """
        return container_ops.has_child(path, key, self.ctx)

    def get_child_type(self, path: TupleKey, key: KeyComponent) -> NodeType:
        """Get type of direct child.

        Args:
            path: Container path
            key: Child key

        Returns:
            NodeType of child

        Example:
            >>> child_type = tree.get_child_type(("users", "alice"), "profile")
        """
        return container_ops.get_child_type(path, key, self.ctx)

    def list_child_keys(self, path: TupleKey) -> Generator[KeyComponent, None, None]:
        """List direct child keys.

        Args:
            path: Container path

        Returns:
            List of child keys

        Example:
            >>> keys = tree.list_child_keys(("users", "alice"))
            >>> print(keys)
            ["profile", "settings", "posts"]
        """
        yield from container_ops.list_child_keys(path, self.ctx)

    def list_child_values(self, path: TupleKey) -> Generator[NodeInfo, None, None]:
        """List direct child keys.

        Args:
            path: Container path

        Returns:
            List of child keys

        Example:
            >>> keys = tree.list_child_keys(("users", "alice"))
            >>> print(keys)
            ["profile", "settings", "posts"]
        """
        yield from container_ops.list_child_values(path, self.ctx)

    def list_children(self, path: TupleKey) -> Generator[tuple[KeyComponent, NodeInfo], None, None]:
        """List all direct children with types.

        Args:
            path: Container path

        Returns:
            List of (child_path, node_type) tuples

        Example:
            >>> children = tree.list_children(("users", "alice"))
            >>> for child_path, node_type in children:
            ...     print(f"{child_path}: {node_type}")
        """
        yield from container_ops.list_children(path, self.ctx)

    def count_children(self, path: TupleKey) -> int:
        """Count direct children.

        Args:
            path: Container path

        Returns:
            Number of direct children

        Example:
            >>> count = tree.count_children(("users", "alice"))
            >>> print(f"{count} children")
        """
        return container_ops.count_children(path, self.ctx)

    def create_child_container(
        self,
        parent_path: TupleKey,
        key: KeyComponent,
        structure: ContainerStructure,
        protocol: ContainerProtocol,
    ) -> bool:
        """Create child container.

        Args:
            parent_path: Parent container path
            key: Child key
            structure: Container structure ID
            protocol: Container protocol flags

        Returns:
            True if created, False if already exists

        Example:
            >>> tree.create_child_container(
            ...     ("users", "alice"),
            ...     "posts",
            ...     ContainerStructure(2),
            ...     ContainerProtocol.MUTABLE,
            ... )
            True
        """
        return container_ops.create_child_container(parent_path, key, structure, protocol, self.ctx)

    def set_child_primitive(
        self,
        parent_path: TupleKey,
        key: KeyComponent,
        value: Value,
    ) -> None:
        """Set primitive child value.

        Args:
            parent_path: Parent container path
            key: Child key
            value: Primitive value

        Example:
            >>> tree.set_child_primitive(("users", "alice"), "name", "Alice Smith")
        """
        container_ops.set_child_primitive(parent_path, key, value, self.ctx)

    def get_child_primitive(
        self,
        parent_path: TupleKey,
        key: KeyComponent,
    ) -> Value | Empty:
        """Get primitive child value.

        Args:
            parent_path: Parent container path
            key: Child key

        Example:
            >>> tree.get_child_primitive(("users", "alice"), "name")
            "Alice Smith"
        """
        return container_ops.get_child_primitive(parent_path, key, self.ctx)

    def delete_child(
        self,
        parent_path: TupleKey,
        key: KeyComponent,
        *,
        recursive: bool = False,
    ) -> bool:
        """Delete direct child.

        Args:
            parent_path: Parent container path
            key: Child key
            recursive: If True and child is container, delete subtree

        Returns:
            True if deleted, False if didn't exist

        Example:
            >>> tree.delete_child(("users", "alice"), "old_profile", recursive=True)
            True
        """
        return container_ops.delete_child(parent_path, key, self.ctx, recursive=recursive)

    def clear_children(self, path: TupleKey) -> int:
        """Delete all direct children.

        Args:
            path: Container path

        Returns:
            Number of children deleted

        Example:
            >>> count = tree.clear_children(("users", "alice", "temp"))
            >>> print(f"Cleared {count} children")
        """
        return container_ops.clear_children(path, self.ctx)

    # ========================================================================
    # RECURSIVE OPERATIONS
    # ========================================================================

    def list_descendants(
        self,
        path: TupleKey,
        *,
        max_depth: int | None = None,
    ) -> list[TupleKey]:
        """List all descendants recursively.

        Args:
            path: Container path
            max_depth: Maximum depth to traverse (None = unlimited)

        Returns:
            List of descendant paths

        Example:
            >>> descendants = tree.list_descendants(("users", "alice"), max_depth=2)
        """
        return container_ops.list_descendants(path, self.ctx, max_depth=max_depth)

    def walk_tree(
        self,
        path: TupleKey,
        *,
        depth_first: bool = True,
    ) -> Generator[tuple[TupleKey, NodeType], None, None]:
        """Iterate over tree structure.

        Args:
            path: Container path
            depth_first: If True, use depth-first traversal

        Yields:
            (path, node_type) tuples

        Example:
            >>> for child_path, node_type in tree.walk_tree(("users", "alice")):
            ...     print(f"{child_path}: {node_type}")
        """
        return container_ops.walk_tree(path, self.ctx, depth_first=depth_first)

    # ========================================================================
    # PARENT MANAGEMENT
    # ========================================================================

    def create_parents(
        self,
        path: TupleKey,
    ) -> list[TupleKey]:
        """Create all missing parents.

        Args:
            path: Target path

        Returns:
            List of created parent paths

        Example:
            >>> created = tree.create_parents(("users", "alice", "profile"))
            >>> print(f"Created {len(created)} parents")
        """
        return container_ops.create_parents(
            path, ContainerStructure(1), ContainerProtocol.MUTABLE, self.ctx
        )

    # ========================================================================
    # NAVIGATION OPERATIONS (Pure functions - no storage access)
    # ========================================================================

    @staticmethod
    def get_parent(path: TupleKey) -> TupleKey | None:
        """Get parent path (pure function).

        Args:
            path: Path to get parent of

        Returns:
            Parent path or None for empty path

        Example:
            >>> parent = Tree.get_parent(("users", "alice"))
            >>> print(parent)
            ("users",)
        """
        return nav.get_parent(path)

    @staticmethod
    def get_ancestors(path: TupleKey) -> list[TupleKey]:
        """Get all ancestors from root to immediate parent (pure function).

        Args:
            path: Path to get ancestors of

        Returns:
            List of ancestor paths

        Example:
            >>> ancestors = Tree.get_ancestors(("users", "alice", "profile"))
            >>> print(ancestors)
            [(), ("users",), ("users", "alice")]
        """
        return nav.get_ancestors(path)

    @staticmethod
    def get_path_chain(path: TupleKey) -> list[TupleKey]:
        """Get complete path chain from root to target (pure function).

        Args:
            path: Target path

        Returns:
            List from root to target (inclusive)

        Example:
            >>> chain = Tree.get_path_chain(("users", "alice"))
            >>> print(chain)
            [(), ("users",), ("users", "alice")]
        """
        return nav.get_path_chain(path)

    @staticmethod
    def is_ancestor(parent: TupleKey, child: TupleKey) -> bool:
        """Check if parent is ancestor of child (pure function).

        Args:
            parent: Potential ancestor path
            child: Potential descendant path

        Returns:
            True if parent is ancestor of child

        Example:
            >>> Tree.is_ancestor(("users",), ("users", "alice"))
            True
        """
        return nav.is_ancestor(parent, child)

    @staticmethod
    def is_descendant(child: TupleKey, parent: TupleKey) -> bool:
        """Check if child is descendant of parent (pure function)."""
        return nav.is_descendant(child, parent)

    @staticmethod
    def is_sibling(path1: TupleKey, path2: TupleKey) -> bool:
        """Check if paths are siblings (pure function)."""
        return nav.is_sibling(path1, path2)

    @staticmethod
    def get_depth(path: TupleKey) -> int:
        """Get depth of path (pure function)."""
        return nav.get_depth(path)

    @staticmethod
    def join_path(*components: KeyComponent | TupleKey) -> TupleKey:
        """Join path components (pure function)."""
        return nav.join_path(*components)

    @staticmethod
    def get_common_ancestor(path1: TupleKey, path2: TupleKey) -> TupleKey:
        """Find lowest common ancestor (pure function)."""
        return nav.get_common_ancestor(path1, path2)
