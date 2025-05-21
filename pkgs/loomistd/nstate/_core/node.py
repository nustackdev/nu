"""
Node implementation for the state management system.

This module defines the abstract Node class, which serves as the base
for all nodes in the state tree.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar, Optional, TypeVar

from .._core.transaction import TransactionalBase
from .._exceptions import ContainerProtocolError
from .._state.backend import ObservableKVBackend, ObservableKVTransaction
from .._types import ContainerProtocol, NodeType
from .._utils import Empty
from .path import StatePath

# Type variable for self-referential typing with TransactionalBase
NodeT = TypeVar("NodeT", bound="Node")

__all__ = ["Node"]


class Node(TransactionalBase[NodeT], ABC):
    """
    Abstract base class for all nodes in the state tree.

    Nodes are the building blocks of the state tree and come in two types:
    - Container nodes: Can contain other nodes (like directories)
    - Primitive nodes: Contain a single value (like files)

    Nodes can be used as context managers for transaction handling:

    Example:
        ```python
        with node as n:
            # Operations on node with transaction
            value = n.some_operation()
        # Transaction automatically committed
        ```
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
        super().__init__()  # Initialize TransactionalBase
        self._backend = backend
        self._path = path
        self._tx = tx  # Override the None from the base class

    @property
    def backend(self) -> ObservableKVBackend:
        """
        Get the backend storage interface.

        Returns:
            ObservableKVBackend: Backend storage interface
        """
        return self._backend

    @property
    def path(self) -> StatePath:
        """
        Get the path of this node.

        Returns:
            StatePath: Path to this node
        """
        return self._path

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
