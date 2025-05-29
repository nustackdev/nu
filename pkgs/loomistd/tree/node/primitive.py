"""
PrimitiveNode implementation for the state management system.

This module defines the PrimitiveNode class, which represents a leaf node
in the state tree that contains a primitive value.
"""

from __future__ import annotations

from functools import cached_property

import attrs

from ..backend import BackendProtocol, TransactionProtocol
from ..path import Path
from ..types import EMPTY, ContainerProtocol, ContainerStructure, Empty, NodeType, Value
from .base import BaseNode
from .container import ContainerNode

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

    @classmethod
    def create(
        cls,
        *,
        backend: BackendProtocol,
        tx: TransactionProtocol,
        path: Path,
    ) -> PrimitiveNode:
        """
        Create a new PrimitiveNode instance.

        Args:
            backend: The backend storage interface
            tx: The transaction to use
            path: The path to the node in the state tree

        Returns:
            PrimitiveNode: A new instance of PrimitiveNode
        """
        return cls(backend=backend, tx=tx, path=path)

    @cached_property
    def parent_container(self) -> ContainerNode:
        """
        Get the parent container of this node.

        Returns:
            BaseNode: Always None for primitive nodes, as they have no parent container
        """
        parent_path = self.path.parent()
        if parent_path is None:
            raise ValueError("Primitive nodes cannot be root nodes")

        parent_container = ContainerNode.create(
            backend=self.backend,
            tx=self.tx,
            path=parent_path,
            structure=ContainerStructure.DEFAULT_CONTAINER,
            protocol=ContainerProtocol.DEFAULT_PROTOCOL,
            ensure_exists=True,
        )
        return parent_container

    @cached_property
    def node_type(self) -> NodeType:
        """
        Get the type of this node.

        Returns:
            NodeType: Always PRIMITIVE for primitive nodes
        """
        return NodeType.PRIMITIVE

    def get_value(self, *, default: Value | Empty = EMPTY) -> Value | Empty:
        """
        Get the primitive value.

        Args:
            tx: Optional transaction (defaults to current transaction)

        Returns:
            Any: Value of the primitive node, or EMPTY if not found
        """
        key = self.path.last()
        if key is None:
            raise ValueError("Cannot get value from a node without a key")

        value = self.parent_container.get_primitive_child(key)

        return default if value is EMPTY else value

    def set_value(self, value: Value, /) -> None:
        """
        Set the primitive value.

        Args:
            value: New value to store
            tx: Optional transaction (defaults to current transaction)
        """
        key = self.path.last()
        if key is None:
            raise ValueError("Cannot get value from a node without a key")
        self.parent_container.set_primitive_child(key, value)

    def remove_value(self) -> bool:
        """
        Delete the primitive value.

        Args:
            tx: Optional transaction (defaults to current transaction)

        Returns:
            bool: True if the value was deleted, False if it did not exist or was not a primitive type
        """
        key = self.path.last()
        if key is None:
            raise ValueError("Cannot delete value from a node without a key")

        return self.parent_container.remove_primitive_child(key)
