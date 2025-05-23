"""
ContainerNode implementation for the state management system.

This module defines the ContainerNode class, which represents a container
node in the state tree that can hold child nodes according to its structure
and protocol specifications.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, cast

import attrs

from loomistd.kv import StorageKeyError

from ..backend import TransactionProtocol
from ..exceptions import ContainerProtocolError, PathTypeError
from ..path import DataPath
from ..transaction import TransactionContext
from ..types import ContainerProtocol, ContainerStructure, NodeType, PathComponent
from .base import BaseNode

__all__ = [
    "ContainerNode",
]


@attrs.define(frozen=True, kw_only=True)
class ContainerNode(BaseNode):
    """
    Container node that can hold child nodes.

    Container nodes represent the structural elements of the state tree,
    similar to directories in a filesystem. They implement specific structures
    and protocols that determine which operations are supported.

    Args:
        backend: Backend storage interface
        path: Path to this node
        structure: Structure supported by this container (MAPPING, SEQUENCE, etc.)
        protocol: Protocol supported by this container (MUTABLE, FLAT, etc.)
        tx: Optional transaction

    Raises:
        ContainerProtocolError: If structure doesn't include CONTAINER
    """

    structure: ContainerStructure = attrs.field(eq=False, hash=False, kw_only=True)

    protocol: ContainerProtocol = attrs.field(eq=False, hash=False, kw_only=True)

    # -------------------------------------------------------------------------
    # Initialization and Base Methods
    # -------------------------------------------------------------------------

    def __post_init__(self) -> None:
        """
        Post-initialization checks.

        Ensures the container node is initialized correctly.
        """
        # Ensure the container node is initialized correctly
        if not self.structure & ContainerStructure.CONTAINER:
            raise ContainerProtocolError("Container nodes must support the CONTAINER structure")

    @property
    def node_type(self) -> NodeType:
        """
        Get the type of this node.

        Returns:
            NodeType: Always CONTAINER for container nodes
        """
        return NodeType.CONTAINER

    @property
    def node_structure(self) -> ContainerStructure:
        """
        Get the structure implemented by this container.

        Returns:
            ContainerStructure: Supported structure
        """
        return self.structure

    @property
    def node_protocol(self) -> ContainerProtocol:
        """
        Get the protocol implemented by this container.

        Returns:
            ContainerProtocol: Supported protocol
        """
        return self.protocol

    # -------------------------------------------------------------------------
    # Support Methods (return boolean)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # Validation Methods (raise exceptions)
    # -------------------------------------------------------------------------

    def validate_mutation(self) -> None:
        """
        Validate that this container supports mutation.

        Raises:
            ContainerProtocolError: If container doesn't support mutation
        """
        self.validate_protocol(ContainerProtocol.MUTABLE)

    def validate_child_path(self, key: PathComponent, node: BaseNode, /) -> None:
        """
        Validate that child node path matches expected path.

        Args:
            key: Key for child
            node: Node to validate

        Raises:
            PathTypeError: If paths don't match
        """
        expected_path = self.path.join(key)
        if expected_path != node.path:
            raise PathTypeError(
                f"Key '{expected_path}' does not match child node path '{node.path}'"
            )

    def validate_flat_constraint(self, node: BaseNode, /) -> None:
        """
        Validate flat container constraint for child node.

        Args:
            node: Node to validate

        Raises:
            ContainerProtocolError: If container is FLAT but node is a container
        """
        if self.protocol & ContainerProtocol.FLAT and node.node_type == NodeType.CONTAINER:
            raise ContainerProtocolError(
                f"Cannot add container child to FLAT container at {self.path}"
            )

    def validate_child_exists(self, key: PathComponent, /) -> None:
        """
        Validate that child exists.

        Args:
            key: Key to check
            tx: Optional transaction

        Raises:
            KeyError: If child doesn't exist
        """
        # Use has_child which handles caching
        with TransactionContext(self.backend, self.tx) as tx:
            if not self.has_child(key):
                raise KeyError(f"No child with key '{key}'")

    def validate_type_field(
        self,
        type_value: Any,
        /,
    ) -> tuple[ContainerStructure, ContainerProtocol]:
        """
        Validate that the node field is of the expected type.

        Args:
            type_value: Value to check
            tx: Optional transaction
        """
        if not isinstance(type_value, (tuple, list)) or len(type_value) != 2:
            raise PathTypeError(f"Node type field is not a valid tuple/list: {type_value}")
        return ContainerStructure(type_value[0]), ContainerProtocol(type_value[1])

    # -------------------------------------------------------------------------
    # Core Operations
    # -------------------------------------------------------------------------

    def exists(
        self,
    ) -> bool:
        """
        Check if this container exists in storage.

        Args:
            tx: Optional transaction

        Returns:
            bool: True if container exists in storage
        """
        with TransactionContext(self.backend, self.tx) as tx:
            try:
                tx.get(self.path.to_tuple())  # Check if the path exists.
                # Note: This is an important check besides the existence,
                # as we also need to enable read tracking for this path
                # to avoid any potential race conditions if the path's been modified
                # in another transaction.
                # For example, in case of rocksdb OptimisticTransaction,
                # an error will be thrown during the commit
                # if the path has been modified in another transaction.

                # Get the type info
                node_info = tx.get(self.path.join(self._TYPE_KEY).to_tuple())

                # Check if the container type info is of the expected type
                structure, protocol = self.validate_type_field(node_info)

                # Verify it's a container and matches the expected structure/protocol
                self.validate_structure(structure)
                self.validate_protocol(protocol)

                return True
            except (StorageKeyError, ContainerProtocolError, PathTypeError):
                return False

        return False

    def ensure_exists(
        self,
    ) -> None:
        """
        Ensure this container exists in storage.

        Creates the container and any necessary parent containers if they don't exist.
        If the container already exists, verifies it's the right type with matching
        structure and protocol.

        Args:
            tx: Optional transaction

        Raises:
            PathTypeError: If path exists but is not a container or has mismatched type
            ContainerProtocolError: If existing container has different structure/protocol
        """
        with TransactionContext(self.backend, self.tx) as tx:
            # Check if already exists
            if self.exists():
                return

            # Ensure parent exists if needed
            parent_path = self.path.parent()
            if parent_path is not None:
                self._ensure_parent_exists(parent_path)

            # Store metadata
            self._store_metadata()

    def has_child(self, key: PathComponent, /) -> bool:
        """
        Check if a child node exists with the given key.

        Args:
            key: Key to check
            tx: Optional transaction

        Returns:
            bool: True if child exists
        """
        with TransactionContext(self.backend, self.tx) as tx:
            child_path = self.path.join(key)
            exists = tx.exists(child_path.to_tuple())
        return exists

    def is_child_container(self, key: PathComponent, /) -> bool:
        """
        Check if a child node is a container.

        Args:
            key: Key to check
            tx: Optional transaction

        Returns:
            bool: True if child exists and is a container
        """
        with TransactionContext(self.backend, self.tx) as tx:
            child_path = self.path.join(key)
            result = self._is_path_container(child_path)
        return result

    def get_child(self, key: PathComponent, /) -> Optional[BaseNode]:
        """
        Get a child node by key.

        Args:
            key: Key of child to retrieve
            tx: Optional transaction

        Returns:
            Node: Child node, or None if no child with that key
        """
        child_node: Optional[BaseNode] = None
        with TransactionContext(self.backend, self.tx) as tx:
            # Check if child exists (using cached method)
            if not self.has_child(key):
                return None

            # Create appropriate node type for the child
            child_path = self.path.join(key)
            child_node = self._create_child_node(child_path)
        return child_node

    def set_child(
        self,
        key: PathComponent,
        child_node: BaseNode,
        /,
        *,
        tx: Optional[TransactionProtocol] = None,
    ) -> BaseNode:
        """
        Set a child node.

        Associates a child node with the given key in this container.

        Args:
            key: Key to associate with the child
            child_node: Node to set as child
            tx: Optional transaction

        Returns:
            Node: The child node that was set

        Raises:
            ContainerProtocolError: If mutation not supported or flat constraint violated
            PathTypeError: If child node path doesn't match expected path
        """
        # Validate constraints
        self.validate_child_path(key, child_node)
        self.validate_mutation()
        self.validate_flat_constraint(child_node)

        with TransactionContext(self.backend, self.tx) as tx:
            # Ensure this container exists
            self.ensure_exists()

            # If the child is a container node, ensure it exists
            if child_node.node_type == NodeType.CONTAINER:
                container_child = cast(ContainerNode, child_node)
                container_child.ensure_exists()
            else:
                # If it's a primitive node
                # do nothing
                pass

            # Update size if needed
            if self.protocol & ContainerProtocol.SIZED and not self.has_child(key):
                self._increment_size()

        return child_node

    def remove_child(self, key: PathComponent, /) -> None:
        """
        Remove a child node.

        Args:
            key: Key of child to remove
            tx: Optional transaction

        Raises:
            ContainerProtocolError: If container doesn't support mutation
            KeyError: If no child exists with that key
        """
        self.validate_mutation()

        with TransactionContext(self.backend, self.tx) as tx:
            # Validate child exists
            self.validate_child_exists(key)

            child_path = self.path.join(key)

            # Remove based on node type
            if self.is_child_container(key):
                self._remove_subtree(child_path)
            else:
                tx.delete(child_path.to_tuple())

            # Update size if needed
            if self.protocol & ContainerProtocol.SIZED:
                self._decrement_size()

    def clear(
        self,
    ) -> None:
        """
        Remove all child nodes.

        Args:
            tx: Optional transaction

        Raises:
            ContainerProtocolError: If container doesn't support mutation
        """
        self.validate_mutation()

        with TransactionContext(self.backend, self.tx) as tx:
            # Get all keys and remove each child
            for key in self.keys():
                child_path = self.path.join(key)

                if self.is_child_container(key):
                    self._remove_subtree(child_path)
                else:
                    tx.delete(child_path.to_tuple())

            # Reset size if container supports SIZED protocol
            if self.protocol & ContainerProtocol.SIZED:
                self._set_size(0)

    def keys(
        self,
    ) -> List[PathComponent]:
        """
        Get all child keys.

        Args:
            tx: Optional transaction

        Returns:
            List[PathComponent]: List of all child keys
        """
        with TransactionContext(self.backend, self.tx) as tx:
            if not self.exists():
                return []

            result = []
            for path in tx.list_keys(self.path.to_tuple(), depth=1):
                key = path[-1]
                if not (isinstance(key, str) and self._MARKER in key):
                    result.append(key)

        return result

    def children(self) -> Dict[PathComponent, BaseNode]:
        """
        Get all child nodes.

        Args:
            tx: Optional transaction

        Returns:
            Dict[PathComponent, Node]: Dictionary mapping keys to child nodes
        """
        with TransactionContext(self.backend, self.tx) as tx:
            result = {}
            for key in self.keys():
                child = self.get_child(key)
                if child is not None:
                    result[key] = child

        return result

    def get_size(
        self,
    ) -> int:
        """
        Get the size of this container.

        Works for any container that supports the SIZED protocol.

        Args:
            tx: Optional transaction

        Returns:
            int: Size of the container, or 0 if not SIZED or size not found
        """
        if not (self.protocol & ContainerProtocol.SIZED):
            return 0

        with TransactionContext(self.backend, self.tx) as tx:
            # Try to get stored size
            size_path = self.path.join(self._SIZE_KEY)
            try:
                size = tx.get(size_path.to_tuple())
                if isinstance(size, int) and size >= 0:
                    return size
            except StorageKeyError:
                pass

            # Compute and store size
            computed_size = len(self.keys())
            self._set_size(computed_size)
            return computed_size
        return 0

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _store_metadata(
        self,
    ) -> None:
        """
        Store container metadata in the backend.

        Args:
            tx: Optional transaction
        """
        with TransactionContext(self.backend, self.tx) as tx:
            # Set the container root
            tx.set(self.path.to_tuple(), None)

            # Store structure and protocol at the type path
            type_path = self.path.join(self._TYPE_KEY)
            node_info = [self.structure.value, self.protocol.value]
            tx.set(type_path.to_tuple(), node_info)

            # Initialize size if container supports SIZED protocol
            if self.protocol & ContainerProtocol.SIZED:
                self._set_size(0)

    def _get_path_type_info(
        self,
        path: DataPath,
        /,
    ) -> Optional[tuple[ContainerStructure, ContainerProtocol]]:
        """
        Get type information for a path.

        Args:
            path: Path to get type info for
            tx: Optional transaction

        Returns:
            Optional[tuple[ContainerStructure, ContainerProtocol]]: Type info if valid, None otherwise
        """
        with TransactionContext(self.backend, self.tx) as tx:
            try:
                type_path = path.join(self._TYPE_KEY)
                node_info = tx.get(type_path.to_tuple())
                return self.validate_type_field(node_info)
            except (StorageKeyError, PathTypeError, ValueError, TypeError):
                return None

    def _ensure_parent_exists(self, parent_path: DataPath, /) -> None:
        """
        Ensure parent container exists.

        Args:
            parent_path: Path to ensure exists
            tx: Optional transaction

        Raises:
            PathTypeError: If parent exists but is invalid
        """
        with TransactionContext(self.backend, self.tx) as tx:
            # Try to get parent type info
            type_info = self._get_path_type_info(parent_path)

            if type_info is not None:
                # Parent exists, validate it's a container
                parent_structure, _ = type_info
                if not parent_structure & ContainerStructure.CONTAINER:
                    raise PathTypeError(f"Parent path {parent_path} exists but is not a container")
                # Parent is valid, nothing more to do
                return

            # Parent doesn't exist or is invalid, create it
            parent = ContainerNode(
                backend=self.backend,
                path=parent_path,
                structure=ContainerStructure.MAPPING_CONTAINER,
                protocol=ContainerProtocol.DICT,
                tx=tx,
            )
            parent.ensure_exists()

    def _create_child_node(self, path: DataPath, /) -> BaseNode:
        """
        Create appropriate node type for path.

        Args:
            path: Path to create node for
            tx: Optional transaction

        Returns:
            Node: Container or primitive node based on stored metadata
        """
        with TransactionContext(self.backend, self.tx) as tx:
            # Try to get type info for the path
            type_info = self._get_path_type_info(path)

            if type_info is not None:
                # It's a container with valid type info
                structure, protocol = type_info
                return ContainerNode(
                    backend=self.backend,
                    path=path,
                    structure=structure,
                    protocol=protocol,
                    tx=tx,
                )
            else:
                # It's a primitive (no valid container type info)
                from .primitive import PrimitiveNode

                return PrimitiveNode(
                    backend=self.backend,
                    path=path,
                    tx=tx,
                )

    def _is_path_container(self, path: DataPath, /) -> bool:
        """
        Check if a path points to a container node.

        Args:
            path: Path to check
            tx: Optional transaction

        Returns:
            bool: True if path points to a container, False otherwise
        """
        with TransactionContext(self.backend, self.tx) as tx:
            type_info = self._get_path_type_info(path)
            if type_info is not None:
                structure, _ = type_info
                return bool(structure & ContainerStructure.CONTAINER)
            return False

    def _increment_size(
        self,
    ) -> None:
        """
        Increment container size by 1.

        Args:
            tx: Optional transaction
        """
        with TransactionContext(self.backend, self.tx) as tx:
            current_size = self.get_size()
            self._set_size(current_size + 1)

    def _decrement_size(
        self,
    ) -> None:
        """
        Decrement container size by 1.

        Args:
            tx: Optional transaction
        """
        with TransactionContext(self.backend, self.tx) as tx:
            current_size = self.get_size()
            if current_size > 0:
                self._set_size(current_size - 1)

    def _set_size(
        self,
        size: int,
        /,
    ) -> None:
        """
        Set the size of this container.

        Args:
            size: New size to set
            tx: Optional transaction
        """
        with TransactionContext(self.backend, self.tx) as tx:
            size_path = self.path.join(self._SIZE_KEY)
            tx.set(size_path.to_tuple(), size)

    def _remove_subtree(self, path: DataPath, /) -> None:
        """
        Recursively remove a subtree.

        Args:
            path: Path to subtree root
            tx: Optional transaction
        """
        with TransactionContext(self.backend, self.tx) as tx:
            # List all descendant paths
            to_delete = []
            for subpath in tx.list_keys(path.to_tuple(), depth=-1):
                to_delete.append(subpath)

            # Sort from longest to shortest to avoid orphans
            to_delete.sort(key=len, reverse=True)

            # Delete all paths
            for p in to_delete:
                try:
                    tx.delete(p)
                except StorageKeyError:
                    pass

            # Delete the root path itself and type metadata
            try:
                type_path = path.join(self._TYPE_KEY)
                tx.delete(type_path.to_tuple())
                tx.delete(path.to_tuple())
            except StorageKeyError:
                pass
