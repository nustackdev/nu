"""
PrimitiveNode implementation for the state management system.

This module defines the PrimitiveNode class, which represents a leaf node
in the state tree that contains a primitive value.
"""

from __future__ import annotations

from typing import Any, Optional

from loomistd.kv import StorageKeyError

from .._state.backend import ObservableKVBackend, ObservableKVTransaction
from .._types import ContainerProtocol, NodeType, StateValue
from .node import Node
from .path import StatePath
from .transaction import TransactionContext

__all__ = ["PrimitiveNode"]


class PrimitiveNode(Node["PrimitiveNode"]):
    """
    Primitive value node (leaf node).

    Primitive nodes represent the leaf values in the state tree,
    similar to files in a filesystem. They contain simple values
    or serialized complex objects.

    Primitive nodes are simply wrappers around values in storage
    and provide methods to get and set those values.

    PrimitiveNode inherits from Node, which implements TransactionalBase, allowing
    it to be used as a context manager for transaction handling.

    Example:
        ```python
        # Create a primitive node
        node = PrimitiveNode(backend, path)

        # Use as context manager for transaction handling
        with node as n:
            n.set_value("Hello, world!")
        # Transaction automatically committed on success or rolled back on exception
        ```
    """

    def __init__(
        self,
        backend: ObservableKVBackend,
        path: StatePath,
        /,
        *,
        tx: Optional[ObservableKVTransaction] = None,
    ) -> None:
        """
        Initialize a primitive node.

        Args:
            backend: Backend storage interface
            path: Path to this node
            tx: Optional transaction
        """
        super().__init__(backend, path, tx=tx)

    def node_type(self) -> NodeType:
        """
        Get the type of this node.

        Returns:
            NodeType: Always PRIMITIVE for primitive nodes
        """
        return NodeType.PRIMITIVE

    def protocols(self) -> ContainerProtocol:
        """
        Get the protocols implemented by this node.

        Returns:
            ContainerProtocol: Empty (no protocols for primitive nodes)
        """
        return ContainerProtocol(0)  # No protocols for primitive nodes

    def get_value(self, *, tx: Optional[ObservableKVTransaction] = None) -> Any:
        """
        Get the primitive value.

        Args:
            tx: Optional transaction (defaults to current transaction)

        Returns:
            Any: Value of the primitive node, or EMPTY if not found
        """
        with TransactionContext(self._backend, tx=tx or self.tx) as tx:
            try:
                result = tx.get(self._path.to_tuple())
            except StorageKeyError:
                # Handle case where the key doesn't exist
                result = self.EMPTY

        return result

    def set_value(
        self, value: StateValue, /, *, tx: Optional[ObservableKVTransaction] = None
    ) -> None:
        """
        Set the primitive value.

        Args:
            value: New value to store
            tx: Optional transaction (defaults to current transaction)
        """
        with TransactionContext(self._backend, tx=tx or self.tx) as tx:
            tx.set(self._path.to_tuple(), value)
