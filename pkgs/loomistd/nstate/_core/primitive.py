"""
PrimitiveNode implementation for the state management system.

This module defines the PrimitiveNode class, which represents a node in the state
tree that contains a primitive value. It provides methods for accessing and modifying
its value.
"""

from __future__ import annotations

from .._types import ContainerProtocol, NodeType, PrimitiveValue
from .node import Node

__all__ = [
    "PrimitiveNode",
]


class PrimitiveNode(Node):
    """
    Primitive value node (leaf node).

    Primitive nodes represent the leaf values in the state tree,
    equivalent to files in a filesystem. They contain simple values
    or serialized complex objects.
    """

    def __init__(self, value: PrimitiveValue) -> None:
        """
        Initialize a primitive node with the given value.

        Args:
            value: The primitive value to store.
        """
        self._value = value

    def node_type(self) -> NodeType:
        """
        Get the type of this node.

        Returns:
            NodeType.PRIMITIVE: Always returns PRIMITIVE for primitive nodes.
        """
        return NodeType.PRIMITIVE

    def protocols(self) -> ContainerProtocol:
        """
        Get the protocols implemented by this node.

        Returns:
            Empty ContainerProtocol: Primitive nodes don't implement any protocols.
        """
        return ContainerProtocol(0)  # No protocols

    @property
    def value(self) -> PrimitiveValue:
        """
        Get the primitive value.

        Returns:
            The stored primitive value.
        """
        return self._value

    @value.setter
    def value(self, new_value: PrimitiveValue) -> None:
        """
        Set the primitive value.

        Args:
            new_value: The new primitive value to store.
        """
        self._value = new_value
