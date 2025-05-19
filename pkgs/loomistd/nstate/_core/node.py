"""
Node implementation for the state management system.

This module defines the abstract Node class, which serves as the base
for all nodes in the state tree.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Callable

from .._core.path import StatePath
from .._exceptions import ContainerProtocolError
from .._state.backend import ObservableKVBackend, ObservableKVTransaction
from .._types import ContainerProtocol, NodeType

__all__ = [
    "Node",
    "with_transaction",
]


class Node(ABC):
    """
    Abstract base class for all nodes in the state tree.

    Nodes are the building blocks of the state tree and come in two types:
    - Container nodes: Can contain other nodes (like directories)
    - Primitive nodes: Contain a single value (like files)

    This class defines the common interface for all nodes and provides
    utility methods for protocol checking.
    """

    # Special markers for node metadata
    _MARKER: str = "\ue000"
    # The Private Use Area (PUA) is a range of Unicode code points (U+E000 to U+F8FF)
    # that are intentionally not assigned to any standard characters.
    # Using PUA characters virtually eliminates the risk of collision since:
    # - They don't appear on standard keyboards
    # - They're not used in any human writing systems
    # - They have no standard visual representation

    _TYPE_KEY: str = _MARKER + "TYPE"
    _PROTOCOLS_KEY: str = _MARKER + "PROTOCOLS"

    def __init__(
        self,
        backend: ObservableKVBackend,
        path: StatePath,
        /,
        *,
        tx: ObservableKVTransaction | None = None,
    ):
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

    @abstractmethod
    def node_type(self) -> NodeType:
        """
        Get the type of this node.

        Returns:
            NodeType.CONTAINER or NodeType.PRIMITIVE
        """
        pass

    @abstractmethod
    def protocols(self) -> ContainerProtocol:
        """
        Get the protocols implemented by this node.

        Returns:
            ContainerProtocol indicating supported protocols
            (Empty for primitive nodes)
        """
        pass

    def supports_protocol(self, protocol: ContainerProtocol, /) -> bool:
        """
        Check if this node supports a specific protocol.

        Args:
            protocol: Protocol to check

        Returns:
            True if protocol is supported, False otherwise
        """
        return bool(self.protocols() & protocol)

    def validate_protocol(self, protocol: ContainerProtocol, /) -> None:
        """
        Validate that this node supports a specific protocol.

        Raises ContainerProtocolError if protocol is not supported.

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


def with_transaction(method: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator for methods that require transaction handling.

    This decorator ensures that a method executes within a transaction.
    It checks for a transaction in the following order:
    1. Transaction passed as a keyword argument ('tx')
    2. Transaction stored in the instance (_tx)
    3. Creates a new transaction if neither is available

    For methods that create a new transaction, the decorator handles
    commit/rollback automatically.

    The 'tx' parameter should always be a keyword-only argument marked
    with '*' in the method signature.

    Example usage:
    ```python
    @with_transaction
    def get_value(self, *, tx=None):
        # Use tx here for storage operations
        return tx.get(self._path)
    ```

    Args:
        method: The method to decorate

    Returns:
        Decorated method with transaction handling
    """

    @wraps(method)
    def wrapper(self: Node, *args, **kwargs):

        # Extract tx from kwargs if present
        tx = kwargs.get("tx")

        # If no tx in kwargs, use instance tx
        if tx is None:
            tx = self._tx

        # If still no tx, create a new one
        created_tx = False
        if tx is None:
            tx = self._backend.begin_transaction()
            created_tx = True

        # Ensure tx is in kwargs for the method call
        kwargs["tx"] = tx

        try:
            # Execute the method with the transaction
            result = method(self, *args, **kwargs)

            # If we created a transaction, commit it
            if created_tx:
                tx.commit()

            return result
        except Exception as e:
            # If we created a transaction, roll it back
            if created_tx:
                tx.rollback()
            raise e

    return wrapper
