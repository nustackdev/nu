"""
ConainerNode implementation for the state management system.

This module defines the ContainerNode class, which represents a node in the state
tree that can contain other nodes. It implements the ContainerProtocol and provides
methods for managing child nodes, including adding, removing, and accessing them.
"""

from __future__ import annotations

from .._exceptions import ContainerProtocolError
from .._types import ContainerProtocol, NodeType, PathComponent
from .node import Node

__all__ = [
    "ContainerNode",
]


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
