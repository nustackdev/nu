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
from .._utils import TransactionContext
from .node import Node
from .path import StatePath

__all__ = ["PrimitiveNode"]


class PrimitiveNode(Node):
    """
    Primitive value node (leaf node).

    Primitive nodes represent the leaf values in the state tree,
    similar to files in a filesystem. They contain simple values
    or serialized complex objects.

    Primitive nodes are simply wrappers around values in storage
    and provide methods to get and set those values.
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
            tx: Optional transaction

        Returns:
            Any: Value of the primitive node, or EMPTY if not found
        """
        with TransactionContext(self._backend, tx or self._tx) as transaction:
            try:
                result = transaction.get(self._path.to_tuple())
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
            tx: Optional transaction
        """
        with TransactionContext(self._backend, tx or self._tx) as transaction:
            transaction.set(self._path.to_tuple(), value)
