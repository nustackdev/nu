"""
PrimitiveNode implementation for the state management system.

This module defines the PrimitiveNode class, which represents a leaf node
in the state tree that contains a primitive value.
"""

from __future__ import annotations

from loomi.interfaces.state.tree import EmptyProtocol
from loomistd.kv._exceptions import StorageKeyError

from .._core.path import StatePath
from .._state.backend import ObservableKVBackend, ObservableKVTransaction
from .._types import ContainerProtocol, NodeType, StateValue
from .node import Node, with_transaction


class Empty(EmptyProtocol):
    """Sentinel object representing an empty value, distinct from None."""

    def __repr__(self) -> str:
        return "<Empty>"


class PrimitiveNode(Node):
    """
    Primitive value node (leaf node).

    Primitive nodes represent the leaf values in the state tree,
    similar to files in a filesystem. They contain simple values
    or serialized complex objects.

    Unlike ContainerNode, PrimitiveNode operations directly affect
    the value at the node's path in the backend storage.
    """

    # Special value for representing empty (but existing) values
    EMPTY = Empty()

    def __init__(
        self,
        backend: ObservableKVBackend,
        path: StatePath,
        /,
        *,
        tx: ObservableKVTransaction | None = None,
    ):
        """
        Initialize a primitive node.

        Args:
            backend: The backend storage interface
            path: Path to this node
            tx: Optional transaction for atomic operations
        """
        super().__init__(backend, path, tx=tx)

    def node_type(self) -> NodeType:
        """
        Get the type of this node.

        Returns:
            NodeType.PRIMITIVE
        """
        return NodeType.PRIMITIVE

    def protocols(self) -> ContainerProtocol:
        """
        Get the protocols implemented by this node.

        Returns:
            Empty ContainerProtocol (no protocols)
        """
        return ContainerProtocol(0)  # No protocols

    @with_transaction
    def get_value(self, *, tx: ObservableKVTransaction) -> StateValue | EmptyProtocol:
        """
        Get the primitive value.

        Args:
            tx: Optional transaction to use

        Returns:
            The stored primitive value or None if not found

        Note:
            Unlike direct backend access, this method returns None
            instead of raising StorageKeyError when the path doesn't exist.
        """
        try:
            return tx.get(self._path.to_tuple())
        except StorageKeyError:
            # Handle case where the key doesn't exist
            return self.EMPTY

    @with_transaction
    def set_value(self, value: StateValue, /, *, tx: ObservableKVTransaction) -> None:
        """
        Set the primitive value.

        Args:
            value: New primitive value to store
            tx: Optional transaction to use
        """
        # Check for parent existence and create if needed
        self._ensure_parent_paths(tx)

        # Store the value
        tx.set(self._path.to_tuple(), value)

    # Property interface for the value
    @property
    def value(self) -> StateValue:
        """
        Get the primitive value.

        Returns:
            The stored primitive value or None if not found
        """
        return self.get_value()

    @value.setter
    def value(self, new_value: StateValue) -> None:
        """
        Set the primitive value.

        Args:
            new_value: New primitive value to store
        """
        self.set_value(new_value)

    @with_transaction
    def _ensure_parent_paths(self, *, tx: ObservableKVTransaction) -> None:
        """
        Ensure parent paths exist.

        Creates parent container nodes if they don't exist.

        Args:
            tx: Optional transaction to use
        """
        # Check if we have a parent path
        parent_path = self._path.parent()
        if parent_path is None:
            # We're at the root, nothing to do
            return

        # Check if parent exists
        if tx.exists(parent_path.to_tuple()):
            # Parent exists, check if it's a container
            parent_type_path = parent_path.join(self._TYPE_KEY)
            try:
                type_value = tx.get(parent_type_path.to_tuple())
                if type_value == "CONTAINER":
                    # Parent is a container, all good
                    return
                # Parent exists but is not a container, this is a type error
                # but we'll let the backend handle it when we try to set the value
            except StorageKeyError:
                # Parent exists but doesn't have a type marker
                # It might be a primitive, but we'll let the backend handle
                # the error when we try to set the value
                pass
        else:
            # Parent doesn't exist, recursively ensure all ancestor paths
            self._ensure_parent_paths(tx=tx)

            # Create parent as a container
            parent_type_path = parent_path.join(self._TYPE_KEY)
            parent_protocols_path = parent_path.join(self._PROTOCOLS_KEY)

            # Use a default MAPPING protocol for auto-created containers
            default_protocols = (
                ContainerProtocol.MAPPING | ContainerProtocol.CONTAINER | ContainerProtocol.MUTABLE
            )

            tx.set(parent_type_path.to_tuple(), "CONTAINER")
            tx.set(parent_protocols_path.to_tuple(), default_protocols.value)
