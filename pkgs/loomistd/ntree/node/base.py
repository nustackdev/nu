"""
Node implementation for the state management system.

This module defines the abstract Node class, which serves as the base
for all nodes in the state tree.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar, Optional

import attrs

from ..backend import BackendProtocol, TransactionProtocol
from ..exceptions import ContainerProtocolError
from ..path import DataPath
from ..types import ContainerProtocol, ContainerStructure, Empty, NodeType

__all__ = [
    "BaseNode",
]


@attrs.define(frozen=True, kw_only=True)
class BaseNode(ABC):
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

    # Path to this node in the state tree
    path: DataPath = attrs.field(eq=False, hash=False, kw_only=True, alias=None)

    # Backend instance for transaction management
    backend: BackendProtocol = attrs.field(eq=False, hash=False, alias=None)

    # Current transaction if any
    tx: Optional[TransactionProtocol] = attrs.field(default=None, eq=False, hash=False, alias=None)

    EMPTY: ClassVar[Empty] = Empty()

    # Special markers for node metadata
    _MARKER: ClassVar[str] = "\ue000"  # Unicode Private Use Area character
    _TYPE_KEY: ClassVar[str] = _MARKER + "T"
    _SIZE_KEY: ClassVar[str] = _MARKER + "S"

    @property
    @abstractmethod
    def node_type(self) -> NodeType:
        """
        Get the type of this node.

        Returns:
            NodeType: CONTAINER or PRIMITIVE
        """
        pass

    @property
    @abstractmethod
    def node_structure(self) -> ContainerStructure:
        """
        Get the structure implemented by this node.

        Returns:
            ContainerStructure: Supported protocol (empty for primitive nodes)
        """
        pass

    @property
    @abstractmethod
    def node_protocol(self) -> ContainerProtocol:
        """
        Get the protocol implemented by this node.

        Returns:
            ContainerProtocol: Supported protocol (empty for primitive nodes)
        """
        pass

    def supports_structure(self, structure: ContainerStructure, /) -> bool:
        """
        Check if this node supports a specific structure.

        Args:
            structure: Structure to check

        Returns:
            bool: True if the structure is supported
        """
        return bool(self.node_structure & structure == structure)

    def supports_protocol(self, protocol: ContainerProtocol, /) -> bool:
        """
        Check if this node supports a specific protocol.

        Args:
            protocol: Protocol to check

        Returns:
            bool: True if the protocol is supported
        """
        return bool(self.node_protocol & protocol)

    def validate_protocol(self, protocol: ContainerProtocol, /) -> None:
        """
        Validate that this node supports a specific protocol.

        Args:
            protocol: Protocol to validate

        Raises:
            ContainerProtocolError: If protocol is not supported
        """
        if not self.supports_protocol(protocol):
            supported = self.node_protocol
            raise ContainerProtocolError(
                f"Node at {self.path} does not support protocol {protocol}. "
                f"Supported protocol: {supported}"
            )

    def validate_structure(self, structure: ContainerStructure, /) -> None:
        """
        Validate that this node supports a specific structure.
        Args:
            structure: Structure to validate
        Raises:
            ContainerProtocolError: If structure is not supported
        """
        if not self.supports_structure(structure):
            supported = self.node_structure
            raise ContainerProtocolError(
                f"Node at {self.path} does not support structure {structure}. "
                f"Supported structure: {supported}"
            )
