"""
Node implementation for the state management system.

This module defines the core node types used in the state tree implementation.
These classes form the underlying structure of the state system and are not
typically accessed directly by users.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .._exceptions import ContainerProtocolError
from .._types import ContainerProtocol, NodeType, PathComponent, PrimitiveValue

__all__ = [
    "Node",
    "ContainerNode",
    "PrimitiveNode",
]


class Node(ABC):
    """
    Abstract base class for all nodes in the state tree.

    Nodes are the building blocks of the state tree, representing either
    containers (which can have children) or primitives (leaf values).
    This is an internal implementation detail, not exposed directly to users.
    """

    @abstractmethod
    def node_type(self) -> NodeType:
        """
        Get the type of this node.

        Returns:
            NodeType: The type of this node (CONTAINER or PRIMITIVE).
        """
        pass

    @abstractmethod
    def protocols(self) -> ContainerProtocol:
        """
        Get the protocols implemented by this node.

        Returns:
            ContainerProtocol: Flag indicating supported protocols.
            For primitive nodes, this will be empty (no protocols).
        """
        pass

    def supports_protocol(self, protocol: ContainerProtocol) -> bool:
        """
        Check if this node supports a specific protocol.

        Args:
            protocol: The protocol to check for support.

        Returns:
            bool: True if the node supports the given protocol.
        """
        return bool(self.protocols() & protocol)

    def validate_protocol(self, protocol: ContainerProtocol) -> None:
        """
        Validate that this node supports a specific protocol.

        Args:
            protocol: The protocol to validate support for.

        Raises:
            ContainerProtocolError: If the node does not support the protocol.
        """
        if not self.supports_protocol(protocol):
            supported = self.protocols()
            raise ContainerProtocolError(
                f"Node does not support protocol {protocol}. " f"Supported: {supported}"
            )


class ContainerNode(Node):
    """
    Container node that can hold child nodes.

    Container nodes represent the structural elements of the state tree,
    equivalent to directories in a filesystem. They implement specific
    protocols that determine which operations are supported.
    """

    def __init__(self, protocols: ContainerProtocol) -> None:
        """
        Initialize a container node with the specified protocols.

        Args:
            protocols: The protocols supported by this container.
                Must include the CONTAINER protocol at minimum.

        Raises:
            ProtocolError: If protocols don't include the CONTAINER protocol.
        """
        if not protocols & ContainerProtocol.CONTAINER:
            raise ContainerProtocolError("Container nodes must support the CONTAINER protocol")
        self._protocols = protocols
        self._children: dict[PathComponent, Node] = {}

    def node_type(self) -> NodeType:
        """
        Get the type of this node.

        Returns:
            NodeType.CONTAINER: Always returns CONTAINER for container nodes.
        """
        return NodeType.CONTAINER

    def protocols(self) -> ContainerProtocol:
        """
        Get the protocols implemented by this container.

        Returns:
            ContainerProtocol: Flag indicating supported protocols.
        """
        return self._protocols

    def get_child(self, key: PathComponent) -> Node | None:
        """
        Get a child node by key.

        Args:
            key: The key of the child node to retrieve.

        Returns:
            The child node, or None if no child exists with that key.
        """
        return self._children.get(key)

    def set_child(self, key: PathComponent, node: Node) -> None:
        """
        Set a child node.

        Args:
            key: The key to associate with the child node.
            node: The node to add as a child.
        """
        self._children[key] = node

    def remove_child(self, key: PathComponent) -> None:
        """
        Remove a child node.

        Args:
            key: The key of the child node to remove.

        Raises:
            KeyError: If no child exists with the given key.
        """
        if key in self._children:
            del self._children[key]
        else:
            raise KeyError(f"No child with key '{key}'")

    def has_child(self, key: PathComponent) -> bool:
        """
        Check if a child node exists.

        Args:
            key: The key to check for.

        Returns:
            True if a child exists with the given key, False otherwise.
        """
        return key in self._children

    def children(self) -> dict[PathComponent, Node]:
        """
        Get all child nodes.

        Returns:
            A dictionary mapping keys to child nodes.
        """
        return self._children.copy()

    def keys(self) -> list[PathComponent]:
        """
        Get all child keys.

        Returns:
            A list of all child keys.
        """
        return list(self._children.keys())

    def clear(self) -> None:
        """
        Remove all child nodes.

        Raises:
            ProtocolError: If the container does not support mutation.
        """
        if not self.supports_protocol(ContainerProtocol.MUTABLE):
            raise ContainerProtocolError("Container does not support mutation")
        self._children.clear()


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
