"""
ContainerNode implementation for the state management system.

This module defines the ContainerNode class, which represents a container
node in the state tree that can hold child nodes according to its protocols.
"""

from __future__ import annotations

from typing import Dict, List, Optional, cast

from loomistd.kv import StorageKeyError

from .._exceptions import ContainerProtocolError, PathTypeError
from .._state.backend import ObservableKVBackend, ObservableKVTransaction
from .._types import CommonContainerProtocols, ContainerProtocol, NodeType, PathComponent
from .node import Node
from .path import StatePath
from .transaction import TransactionContext

__all__ = ["ContainerNode"]


class ContainerNode(Node["ContainerNode"]):
    """
    Container node that can hold child nodes.

    Container nodes represent the structural elements of the state tree,
    similar to directories in a filesystem. They implement specific protocols
    that determine which operations are supported.

    ContainerNode inherits from Node, which implements TransactionalBase, allowing
    it to be used as a context manager for transaction handling.

    Example:
        ```python
        # Create a container node
        container = ContainerNode(backend, path, protocols)

        # Use as context manager for transaction handling
        with container as c:
            c.ensure_exists()
            c.set_child("key", value)
        # Transaction automatically committed on success or rolled back on exception
        ```
    """

    # Special markers for list operations
    _LIST_LENGTH_KEY: str = Node._MARKER + "LIST_LENGTH"

    def __init__(
        self,
        backend: ObservableKVBackend,
        path: StatePath,
        protocols: ContainerProtocol,
        /,
        *,
        tx: Optional[ObservableKVTransaction] = None,
    ) -> None:
        """
        Initialize a container node.

        Args:
            backend: Backend storage interface
            path: Path to this node
            protocols: Protocols supported by this container
            tx: Optional transaction

        Raises:
            ContainerProtocolError: If protocols don't include CONTAINER
        """
        if not protocols & ContainerProtocol.CONTAINER:
            raise ContainerProtocolError("Container nodes must support the CONTAINER protocol")

        super().__init__(backend, path, tx=tx)

        self._protocols = protocols

    def node_type(self) -> NodeType:
        """
        Get the type of this node.

        Returns:
            NodeType: Always CONTAINER for container nodes
        """
        return NodeType.CONTAINER

    def protocols(self, *, tx: ObservableKVTransaction | None = None) -> ContainerProtocol:
        """
        Get the protocols implemented by this container.

        If the container exists in storage, retrieves the protocols from storage.
        Otherwise, returns the in-memory protocols.

        Args:
            tx: Optional transaction (defaults to current transaction)

        Returns:
            ContainerProtocol: Supported protocols
        """
        with TransactionContext(self._backend, tx=tx or self.tx) as tx:
            protocols_path = self._path.join(self._PROTOCOLS_KEY)
            try:
                protocols_value = tx.get(protocols_path.to_tuple())
                result = ContainerProtocol(protocols_value)
            except (StorageKeyError, ValueError):
                result = self._protocols

        return result

    def exists(self, *, tx: ObservableKVTransaction | None = None) -> bool:
        """
        Check if this container exists in storage.

        Args:
            tx: Optional transaction (defaults to current transaction)

        Returns:
            bool: True if container exists in storage
        """
        with TransactionContext(self._backend, tx=tx or self.tx) as tx:
            # Check if path exists
            if not tx.exists(self._path.to_tuple()):
                result = False
            else:
                # Verify it's a container by checking type marker
                type_path = self._path.join(self._TYPE_KEY)
                try:
                    type_value = tx.get(type_path.to_tuple())
                    result = type_value == self._TYPE_CONTAINER
                except StorageKeyError:
                    result = False

        return result

    def ensure_exists(self, *, tx: ObservableKVTransaction | None = None) -> None:
        """
        Ensure this container exists in storage.

        Creates the container and any necessary parent containers if they don't exist.
        If the container already exists, verifies it's the right type.

        Args:
            tx: Optional transaction (defaults to current transaction)

        Raises:
            PathTypeError: If path exists but is not a container
        """
        with TransactionContext(self._backend, tx=tx or self.tx) as tx:
            # Check if already exists
            if tx.exists(self._path.to_tuple()):
                # Verify it's a container
                type_path = self._path.join(self._TYPE_KEY)
                try:
                    type_value = tx.get(type_path.to_tuple())
                    if type_value != self._TYPE_CONTAINER:
                        raise PathTypeError(f"Path {self._path} exists but is not a container")
                except StorageKeyError:
                    raise PathTypeError(f"Path {self._path} exists but doesn't have type metadata")

                # Update protocols if needed
                self._store_metadata(tx=tx)
                return

            # Ensure parent exists
            parent_path = self._path.parent()
            if parent_path is not None and not parent_path.is_root():
                # Check if parent exists
                if not tx.exists(parent_path.to_tuple()):
                    # Create parent container
                    parent = ContainerNode(
                        self._backend, parent_path, CommonContainerProtocols.DICT, tx=tx
                    )
                    parent.ensure_exists(tx=tx)
                else:
                    # Verify parent is a container
                    parent_type_path = parent_path.join(self._TYPE_KEY)
                    try:
                        type_value = tx.get(parent_type_path.to_tuple())
                        if type_value != self._TYPE_CONTAINER:
                            raise PathTypeError(
                                f"Parent path {parent_path} exists but is not a container"
                            )
                    except StorageKeyError:
                        raise PathTypeError(
                            f"Parent path {parent_path} exists but doesn't have type metadata"
                        )

            # Store container metadata
            self._store_metadata(tx=tx)

    def _store_metadata(self, *, tx: ObservableKVTransaction) -> None:
        """
        Store container metadata in the backend.

        Args:
            tx: Transaction to use
        """
        type_path = self._path.join(self._TYPE_KEY)
        protocols_path = self._path.join(self._PROTOCOLS_KEY)

        with TransactionContext(self._backend, tx=tx or self.tx) as tx:
            tx.set(self._path.to_tuple(), None)
            tx.set(type_path.to_tuple(), self._TYPE_CONTAINER)
            tx.set(protocols_path.to_tuple(), self._protocols.value)

    def update_protocols(
        self, protocols: ContainerProtocol, /, *, tx: Optional[ObservableKVTransaction] = None
    ) -> None:
        """
        Update the protocols supported by this container.

        Args:
            protocols: New protocols to support
            tx: Optional transaction (defaults to current transaction)

        Raises:
            ContainerProtocolError: If new protocols don't include CONTAINER
        """
        if not protocols & ContainerProtocol.CONTAINER:
            raise ContainerProtocolError("Container nodes must support the CONTAINER protocol")

        self._protocols = protocols

        with TransactionContext(self._backend, tx=tx or self.tx) as tx:
            protocols_path = self._path.join(self._PROTOCOLS_KEY)
            tx.set(protocols_path.to_tuple(), protocols.value)

    def has_child(
        self, key: PathComponent, /, *, tx: Optional[ObservableKVTransaction] = None
    ) -> bool:
        """
        Check if a child node exists with the given key.

        Args:
            key: Key to check
            tx: Optional transaction (defaults to current transaction)

        Returns:
            bool: True if child exists
        """
        with TransactionContext(self._backend, tx=tx or self.tx) as tx:
            child_path = self._path.join(key)
            result = tx.exists(child_path.to_tuple())

        return result

    def get_child(
        self, key: PathComponent, /, *, tx: Optional[ObservableKVTransaction] = None
    ) -> Optional[Node]:
        """
        Get a child node by key.

        Args:
            key: Key of child to retrieve
            tx: Optional transaction (defaults to current transaction)

        Returns:
            Node: Child node, or None if no child with that key
        """
        with TransactionContext(self._backend, tx=tx or self.tx) as tx:
            child_path = self._path.join(key)

            # Check if child exists
            if not tx.exists(child_path.to_tuple()):
                node = None
            else:
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

                        # Return container node
                        node = ContainerNode(self._backend, child_path, protocols, tx=tx)
                    else:
                        # Not a container, treat as primitive
                        from .primitive import PrimitiveNode

                        node = PrimitiveNode(self._backend, child_path, tx=tx)
                except StorageKeyError:
                    # No type metadata, treat as primitive
                    from .primitive import PrimitiveNode

                    node = PrimitiveNode(self._backend, child_path, tx=tx)

        return node

    def set_child(
        self,
        key: PathComponent,
        child_node: Node,
        /,
        *,
        tx: Optional[ObservableKVTransaction] = None,
    ) -> Node | None:
        """
        Set a child node.

        Associates a child node with the given key in this container.

        Args:
            key: Key to associate with the child
            child_node: Node to set as child
            tx: Optional transaction (defaults to current transaction)

        Returns:
            Node: The child node that was set

        Raises:
            ContainerProtocolError: If container doesn't support mutation
            PathTypeError: If child node path doesn't match expected path
        """
        from .primitive import PrimitiveNode

        if self.path.join(key) != child_node.path:
            raise PathTypeError(
                f"Key '{self.path.join(key)}' does not match child node path '{child_node.path}'"
            )

        with TransactionContext(self._backend, tx=tx or self.tx) as tx:
            # Validate container supports mutation
            if not self.supports_protocol(ContainerProtocol.MUTABLE):
                raise ContainerProtocolError(f"Container at {self._path} does not support mutation")

            # Ensure container exists
            self.ensure_exists()

            if child_node.node_type() == NodeType.CONTAINER:
                # Get the container's protocols
                child_node = cast(ContainerNode, child_node)
                child_node.ensure_exists(tx=tx)
            elif child_node.node_type() == NodeType.PRIMITIVE:
                # It's a primitive node, just return it
                child_node = cast(PrimitiveNode, child_node)
        return child_node

    def remove_child(
        self, key: PathComponent, /, *, tx: Optional[ObservableKVTransaction] = None
    ) -> None:
        """
        Remove a child node.

        Args:
            key: Key of child to remove
            tx: Optional transaction (defaults to current transaction)

        Raises:
            ContainerProtocolError: If container doesn't support mutation
            KeyError: If no child exists with that key
        """
        with TransactionContext(self._backend, tx=tx or self.tx) as tx:
            # Validate container supports mutation
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
                    self._remove_subtree(child_path, tx=tx)
                    return
            except StorageKeyError:
                # No type metadata or not a container
                pass

            # It's a primitive or doesn't exist, just remove it
            tx.delete(child_path.to_tuple())

    def keys(self, *, tx: Optional[ObservableKVTransaction] = None) -> List[PathComponent]:
        """
        Get all child keys.

        Args:
            tx: Optional transaction (defaults to current transaction)

        Returns:
            List[PathComponent]: List of all child keys
        """
        with TransactionContext(self._backend, tx=tx or self.tx) as tx:
            # Ensure container exists
            if not self.exists(tx=tx):
                return []

            result = []

            # List all direct children of this path
            for path in tx.list_keys(self._path.to_tuple(), depth=1):
                # Get the key (last component)
                key = path[-1]

                # Skip metadata keys (those with our special marker)
                if isinstance(key, str) and self._MARKER in key:
                    continue

                # Add to result if not already included
                if key not in result:
                    result.append(key)

        return result

    def children(
        self, *, tx: Optional[ObservableKVTransaction] = None
    ) -> Dict[PathComponent, Node]:
        """
        Get all child nodes.

        Args:
            tx: Optional transaction (defaults to current transaction)

        Returns:
            Dict[PathComponent, Node]: Dictionary mapping keys to child nodes
        """
        with TransactionContext(self._backend, tx=tx or self.tx) as tx:
            result = {}

            for key in self.keys(tx=tx):
                child = self.get_child(key, tx=tx)
                if child is not None:
                    result[key] = child

        return result

    def clear(self, *, tx: Optional[ObservableKVTransaction] = None) -> None:
        """
        Remove all child nodes.

        Args:
            tx: Optional transaction (defaults to current transaction)

        Raises:
            ContainerProtocolError: If container doesn't support mutation
        """
        with TransactionContext(self._backend, tx=tx or self.tx) as tx:
            # Validate container supports mutation
            if not self.supports_protocol(ContainerProtocol.MUTABLE):
                raise ContainerProtocolError(f"Container at {self._path} does not support mutation")

            # Get all keys and remove each child
            keys_to_remove = self.keys(tx=tx)
            for key in keys_to_remove:
                self.remove_child(key, tx=tx)

    def _remove_subtree(self, path: StatePath, /, *, tx: ObservableKVTransaction) -> None:
        """
        Recursively remove a subtree.

        Args:
            path: Path to subtree root
            tx: Transaction to use
        """
        with TransactionContext(self._backend, tx=tx or self.tx) as tx:
            # List all keys under this path (unlimited depth)
            to_delete = []
            for subpath in tx.list_keys(path.to_tuple(), depth=-1):
                to_delete.append(subpath)

            # Delete all paths (from longest to shortest to avoid orphans)
            to_delete.sort(key=len, reverse=True)
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
