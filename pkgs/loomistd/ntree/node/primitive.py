"""
PrimitiveNode implementation for the state management system.

This module defines the PrimitiveNode class, which represents a leaf node
in the state tree that contains a primitive value.
"""

from __future__ import annotations

from typing import Any, Optional

import attrs

from loomistd.kv import StorageKeyError

from ..backend import TransactionProtocol
from ..transaction import with_transaction
from ..types import NodeType, Value
from .base import BaseNode

__all__ = ["PrimitiveNode"]


@attrs.define(frozen=True, kw_only=True)
class PrimitiveNode(BaseNode):
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

    @property
    def node_type(self) -> NodeType:
        """
        Get the type of this node.

        Returns:
            NodeType: Always PRIMITIVE for primitive nodes
        """
        return NodeType.PRIMITIVE

    def get_value(self, *, tx: Optional[TransactionProtocol] = None) -> Any:
        """
        Get the primitive value.

        Args:
            tx: Optional transaction (defaults to current transaction)

        Returns:
            Any: Value of the primitive node, or EMPTY if not found
        """
        with with_transaction(self) as node:
            tx = node.get_ensured_transaction()

            try:
                result = tx.get(node.path.to_tuple())
            except StorageKeyError:
                # Handle case where the key doesn't exist
                result = node.EMPTY

        return result

    def set_value(self, value: Value, /, *, tx: Optional[TransactionProtocol] = None) -> None:
        """
        Set the primitive value.

        Args:
            value: New value to store
            tx: Optional transaction (defaults to current transaction)
        """
        with with_transaction(self) as node:
            tx = node.get_ensured_transaction()
            tx.set(node.path.to_tuple(), value)
