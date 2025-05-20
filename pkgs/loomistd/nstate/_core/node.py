"""
Node implementation for the state management system.

This module defines the abstract Node class, which serves as the base
for all nodes in the state tree.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar, Optional

from .._exceptions import ContainerProtocolError
from .._state.backend import ObservableKVBackend, ObservableKVTransaction
from .._types import ContainerProtocol, NodeType
from .._utils import Empty
from .path import StatePath

__all__ = ["Node"]


class Node(ABC):
    """
    Abstract base class for all nodes in the state tree.

    Nodes are the building blocks of the state tree and come in two types:
    - Container nodes: Can contain other nodes (like directories)
    - Primitive nodes: Contain a single value (like files)
    """

    EMPTY: Empty = Empty()

    # Special markers for node metadata
    _MARKER: ClassVar[str] = "\ue000"  # Unicode Private Use Area character
    _TYPE_KEY: ClassVar[str] = _MARKER + "TYPE"
    _PROTOCOLS_KEY: ClassVar[str] = _MARKER + "PROTOCOLS"

    # Container type marker values
    _TYPE_CONTAINER: ClassVar[str] = "CONTAINER"
    _TYPE_PRIMITIVE: ClassVar[str] = "PRIMITIVE"

    def __init__(
        self,
        backend: ObservableKVBackend,
        path: StatePath,
        /,
        *,
        tx: Optional[ObservableKVTransaction] = None,
    ) -> None:
        """
        Initialize a node.

        Args:
            backend: The backend storage interface
            path: Path to this node
            tx: Optional transaction for atomic operations
        """
        self._backend = backend
        self._path = path
        self._tx = tx

    @property
    def path(self) -> StatePath:
        """
        Get the path of this node.

        Returns:
            StatePath: Path to this node
        """
        return self._path

    @property
    def backend(self) -> ObservableKVBackend:
        """
        Get the backend of this node.

        Returns:
            ObservableKVBackend: Backend storage interface
        """
        return self._backend

    @abstractmethod
    def node_type(self) -> NodeType:
        """
        Get the type of this node.

        Returns:
            NodeType: CONTAINER or PRIMITIVE
        """
        pass

    @abstractmethod
    def protocols(self) -> ContainerProtocol:
        """
        Get the protocols implemented by this node.

        Returns:
            ContainerProtocol: Supported protocols (empty for primitive nodes)
        """
        pass

    def supports_protocol(self, protocol: ContainerProtocol, /) -> bool:
        """
        Check if this node supports a specific protocol.

        Args:
            protocol: Protocol to check

        Returns:
            bool: True if the protocol is supported
        """
        return bool(self.protocols() & protocol)

    def validate_protocol(self, protocol: ContainerProtocol, /) -> None:
        """
        Validate that this node supports a specific protocol.

        Args:
            protocol: Protocol to validate

        Raises:
            ContainerProtocolError: If protocol is not supported
        """
        if not self.supports_protocol(protocol):
            supported = self.protocols()
            raise ContainerProtocolError(
                f"Node at {self._path} does not support protocol {protocol}. "
                f"Supported protocols: {supported}"
            )
