"""
ContainerNode implementation for the state management system.

This module defines the ContainerNode class, which represents a container
node in the state tree that can hold child nodes.
"""

from __future__ import annotations

from typing import Dict, List, Optional, cast

from loomistd.kv import StorageKeyError

from .._core.path import StatePath
from .._exceptions import ContainerProtocolError
from .._state.backend import ObservableKVBackend, ObservableKVTransaction
from .._types import ContainerProtocol, NodeType, PathComponent
from .node import Node, with_transaction
from .primitive import PrimitiveNode


class ContainerNode(Node):
    """
    Container node that can hold child nodes.

    Container nodes represent the structural elements of the state tree,
    similar to directories in a filesystem. They implement specific protocols
    that determine which operations are supported.

    Instead of storing children in memory, this implementation uses the
    backend storage directly for all operations.
    """

    # Container type marker values
    _TYPE_CONTAINER: str = "CONTAINER"

    # Special markers for list operations
    _LIST_LENGTH_KEY: str = Node._MARKER + "LIST_LENGTH"

    def __init__(
        self,
        backend: ObservableKVBackend,
        path: StatePath,
        protocols: ContainerProtocol,
        /,
        *,
        tx: ObservableKVTransaction | None = None,
    ):
        """
        Initialize a container node with specified protocols.

        Args:
            backend: The backend storage interface
            path: Path to this node
            protocols: Protocols supported by this container
            tx: Optional transaction for atomic operations

        Raises:
            ContainerProtocolError: If protocols don't include CONTAINER
        """
        super().__init__(backend, path, tx=tx)

        if not protocols & ContainerProtocol.CONTAINER:
            raise ContainerProtocolError("Container nodes must support the CONTAINER protocol")

        self._protocols = protocols

        # Store node metadata in backend
        self._store_metadata(tx=tx)

    def node_type(self) -> NodeType:
        """
        Get the type of this node.

        Returns:
            NodeType.CONTAINER
        """
        return NodeType.CONTAINER

    @with_transaction
    def protocols(
        self,
        *,
        tx: ObservableKVTransaction,
    ) -> ContainerProtocol:
        """
        Get the protocols implemented by this container.

        Args:
            tx: Optional transaction to use

        Returns:
            ContainerProtocol flags indicating supported protocols
        """
        # Try to get from backend first, fall back to instance variable
        protocols_path = self._path.join(self._PROTOCOLS_KEY)
        try:
            protocols_value = tx.get(protocols_path.to_tuple())
            return ContainerProtocol(protocols_value)
        except (StorageKeyError, ValueError):
            return self._protocols

    @with_transaction
    def get_child(
        self,
        key: PathComponent,
        /,
        *,
        tx: ObservableKVTransaction,
    ) -> Optional[Node]:
        """
        Get a child node by key.

        Args:
            key: Key of the child node to retrieve
            tx: Optional transaction to use

        Returns:
            The child node, or None if no child exists with that key
        """
        child_path = self._path.join(key)

        # Check if child exists
        if not tx.exists(child_path.to_tuple()):
            return None

        # Determine child type
        type_path = child_path.join(self._TYPE_KEY)
        try:
            node_type_value = tx.get(type_path.to_tuple())
            if node_type_value == self._TYPE_CONTAINER:
                # Get container protocols
                protocols_path = child_path.join(self._PROTOCOLS_KEY)
                try:
                    protocols_value = tx.get(protocols_path.to_tuple())
                    protocols = ContainerProtocol(protocols_value)
                except (StorageKeyError, ValueError):
                    # Default to basic container
                    protocols = ContainerProtocol.CONTAINER

                return ContainerNode(self._backend, child_path, protocols, tx=tx)
        except StorageKeyError:
            # No type metadata or not a container
            pass

        # Treat as primitive
        return PrimitiveNode(self._backend, child_path, tx=tx)

    @with_transaction
    def set_child(
        self,
        key: PathComponent,
        node: Node,
        /,
        *,
        tx: ObservableKVTransaction,
    ) -> None:
        """
        Set a child node.

        Args:
            key: Key to associate with the child node
            node: Node to add as a child
            tx: Optional transaction to use

        Raises:
            ContainerProtocolError: If container doesn't support mutation
        """
        if not self.supports_protocol(ContainerProtocol.MUTABLE):
            raise ContainerProtocolError(f"Container at {self._path} does not support mutation")

        child_path = self._path.join(key)

        if isinstance(node, ContainerNode):
            # It's a container, copy its metadata
            container_node = cast(ContainerNode, node)

            # Store type and protocols
            type_path = child_path.join(self._TYPE_KEY)
            protocols_path = child_path.join(self._PROTOCOLS_KEY)

            tx.set(type_path.to_tuple(), self._TYPE_CONTAINER)
            tx.set(protocols_path.to_tuple(), container_node.protocols().value)

            # We don't need to copy children - they'll be accessed via the path
        elif isinstance(node, PrimitiveNode):
            # It's a primitive, store its value
            primitive_node = cast(PrimitiveNode, node)
            tx.set(child_path.to_tuple(), primitive_node.value)
        else:
            raise TypeError(f"Unsupported node type: {type(node)}")

    @with_transaction
    def remove_child(
        self,
        key: PathComponent,
        /,
        *,
        tx: ObservableKVTransaction,
    ) -> None:
        """
        Remove a child node.

        For container children, recursively removes all descendants.

        Args:
            key: Key of the child node to remove
            tx: Optional transaction to use

        Raises:
            KeyError: If no child exists with the given key
            ContainerProtocolError: If container doesn't support mutation
        """
        if not self.supports_protocol(ContainerProtocol.MUTABLE):
            raise ContainerProtocolError(f"Container at {self._path} does not support mutation")

        child_path = self._path.join(key)

        # Check if child exists
        if not tx.exists(child_path.to_tuple()):
            raise KeyError(f"No child with key '{key}'")

        # Check if it's a container by testing for the type key
        type_path = child_path.join(self._TYPE_KEY)
        try:
            node_type_value = tx.get(type_path.to_tuple())
            if node_type_value == self._TYPE_CONTAINER:
                # It's a container, recursively remove all descendants
                self._remove_subtree(tx, child_path)
                return
        except StorageKeyError:
            # No type metadata or not a container
            pass

        # It's a primitive or doesn't exist, just remove it
        tx.delete(child_path.to_tuple())

    @with_transaction
    def has_child(
        self,
        key: PathComponent,
        /,
        *,
        tx: ObservableKVTransaction,
    ) -> bool:
        """
        Check if a child node exists.

        Args:
            key: Key to check for
            tx: Optional transaction to use

        Returns:
            True if a child exists with the given key, False otherwise
        """
        child_path = self._path.join(key)
        return tx.exists(child_path.to_tuple())

    @with_transaction
    def children(
        self,
        *,
        tx: ObservableKVTransaction,
    ) -> Dict[PathComponent, Node]:
        """
        Get all child nodes.

        Args:
            tx: Optional transaction to use

        Returns:
            Dictionary mapping keys to child nodes
        """
        result = {}

        # Get all direct children
        for key in self.keys(tx=tx):
            child = self.get_child(key, tx=tx)
            if child:
                result[key] = child

        return result

    @with_transaction
    def keys(
        self,
        *,
        tx: ObservableKVTransaction,
    ) -> List[PathComponent]:
        """
        Get all child keys.

        Args:
            tx: Optional transaction to use

        Returns:
            List of all child keys
        """
        result = []

        # List all direct children of this path
        len(self._path.components)
        for path in tx.list_keys(self._path.to_tuple(), depth=1):
            # Get the key (last component)
            key = path[-1]

            # Skip metadata keys (those with our special marker)
            if self._MARKER in key:
                continue

            # Add to result if not already included
            if key not in result:
                result.append(key)

        return result

    @with_transaction
    def clear(
        self,
        *,
        tx: ObservableKVTransaction,
    ) -> None:
        """
        Remove all child nodes.

        Args:
            tx: Optional transaction to use

        Raises:
            ContainerProtocolError: If container doesn't support mutation
        """
        if not self.supports_protocol(ContainerProtocol.MUTABLE):
            raise ContainerProtocolError(f"Container at {self._path} does not support mutation")

        # Remove each child
        for key in list(self.keys(tx=tx)):
            self.remove_child(key, tx=tx)

    @with_transaction
    def _store_metadata(
        self,
        *,
        tx: ObservableKVTransaction,
    ) -> None:
        """
        Store node metadata in the backend.

        Args:
            tx: Optional transaction to use

        Sets the type and protocols for this container.
        """
        type_path = self._path.join(self._TYPE_KEY)
        protocols_path = self._path.join(self._PROTOCOLS_KEY)

        tx.set(type_path.to_tuple(), self._TYPE_CONTAINER)
        tx.set(protocols_path.to_tuple(), self._protocols.value)

    @with_transaction
    def _remove_subtree(
        self,
        path: StatePath,
        /,
        *,
        tx: ObservableKVTransaction,
    ) -> None:
        """
        Recursively remove a subtree.

        Removes the node at the given path and all its descendants.

        Args:
            tx: Transaction to use (required)
            path: Path to the subtree root
        """
        # Collect all paths to delete
        to_delete = []

        # List all keys under this path (unlimited depth)
        for subpath in tx.list_keys(path.to_tuple(), depth=-1):
            to_delete.append(subpath)

        # Delete all paths (from longest to shortest to avoid orphans)
        to_delete.sort(key=lambda p: len(p.components), reverse=True)
        for p in to_delete:
            try:
                tx.delete(p)
            except StorageKeyError:
                # May have been already deleted as part of parent deletion
                pass

        # Delete the root path itself
        try:
            tx.delete(path.to_tuple())
        except StorageKeyError:
            pass
