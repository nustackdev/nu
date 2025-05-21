"""
Base view implementation for the state management system.

This module defines the BaseView class, which provides common functionality
for all view implementations. Views provide protocol-specific interfaces
for interacting with container nodes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, List, Optional, cast

from .._core.container import ContainerNode
from .._core.node import Node
from .._core.path import StatePath
from .._core.primitive import PrimitiveNode
from .._core.transaction import TransactionalBase, TransactionContext
from .._exceptions import ContainerProtocolError, IncompatibleViewError
from .._state.backend import ObservableKVBackend, ObservableKVTransaction
from .._types import CommonContainerProtocols, ContainerProtocol, NodeType, PathComponent, ViewT
from .._utils import is_empty

if TYPE_CHECKING:
    from .._state.state import State

__all__ = ["BaseView"]


class BaseView(TransactionalBase[ViewT], ABC):
    """
    Base class for all container views.

    Views provide protocol-specific interfaces for interacting with
    container nodes. Each view type implements specific operations
    appropriate for a particular container protocol.

    The BaseView provides common functionality used by all view types,
    including protocol validation, path access, and navigation.

    Example:
        ```python
        # Using a view with a context manager (auto transaction)
        with state.at("users").dict_view() as users:
            users.set("alice", {"name": "Alice"})
            users.set("bob", {"name": "Bob"})

        # Using a view with an explicit transaction
        tx = state.begin_transaction()
        try:
            users = state.at("users").dict_view(tx=tx)
            users.set("alice", {"name": "Alice"})
            tx.commit()
        except Exception:
            tx.rollback()
            raise
        ```
    """

    @staticmethod
    @abstractmethod
    def required_protocols() -> ContainerProtocol:
        """
        Get the protocols required by this view.

        Must be implemented by each view type to specify which
        container protocols it requires.

        Returns:
            ContainerProtocol: Required protocols
        """
        pass

    def __init__(
        self,
        container: ContainerNode,
        /,
        *,
        tx: Optional[ObservableKVTransaction] = None,
    ) -> None:
        """
        Initialize a view for a container.

        Args:
            container: Container node to view
            tx: Optional transaction

        Raises:
            IncompatibleViewError: If container doesn't support required protocols
        """
        super().__init__()
        self._container = container
        self._tx = tx

        with TransactionContext(self.backend, tx=self.tx) as tx:
            # Ensure container exists with required protocols
            container.ensure_exists(tx=tx)

            # Validate container supports required protocols
            required = self.required_protocols()
            supported = container.protocols(tx=tx)

            # Check if container supports all required protocols
            if (supported & required) != required:
                missing = [p for p in ContainerProtocol if p & required and not (p & supported)]
                raise IncompatibleViewError(
                    f"Container at {container.path} does not support required protocols: {missing}"
                )

    @property
    def backend(self) -> ObservableKVBackend:
        """
        Get the backend storage interface.

        Returns:
            ObservableKVBackend: Backend storage interface
        """
        return self._container.backend

    @property
    def container(self) -> ContainerNode:
        """
        Get the underlying container node.

        Returns:
            ContainerNode: Container node
        """
        return self._container

    @property
    def path(self) -> StatePath:
        """
        Get the path of this view.

        Returns:
            StatePath: Path to the container
        """
        return self._container.path

    def exists(self) -> bool:
        """
        Check if the container exists.

        Returns:
            bool: True if container exists
        """
        with TransactionContext(self.backend, tx=self.tx) as tx:
            exists = self._container.exists(tx=tx)
        return exists

    def keys(self) -> List[PathComponent]:
        """
        Get all keys in the container.

        Returns:
            List[PathComponent]: List of keys
        """
        with TransactionContext(self.backend, tx=self.tx) as tx:
            keys = self._container.keys(tx=tx)
        return keys

    def root(self, *, tx: Optional[ObservableKVTransaction] = None) -> "State":
        """
        Navigate to root path.

        Returns:
            State: State for the root path

        Example:
            ```python
            deep_dict = state.at("deeply", "nested", "path").dict_view()
            root_state = deep_dict.root()  # State for root
            ```
        """
        # Import here to avoid circular imports
        from .._state.state import State

        # Create State for root path
        return State(self.backend, StatePath(), tx=tx)

    def _extract_value(self, node: Node, /, *, recursive: bool = True) -> Any:
        """
        Extract a value from a node.

        Handles both primitive and container nodes, with optional recursion for containers.

        Args:
            node: Node to extract value from
            recursive: Whether to recursively extract container values

        Returns:
            Any: Python representation of the node's value
        """
        with TransactionContext(self.backend, tx=self.tx) as tx:
            if node.node_type() == NodeType.PRIMITIVE:
                # Get primitive value
                primitive = cast(PrimitiveNode, node)
                value = primitive.get_value(tx=tx)
                return None if is_empty(value) else value

            # For container nodes
            if not recursive:
                # Just return the node if not recursing
                return node

            # Recursive extraction for container nodes
            container = cast(ContainerNode, node)
            result = {}

            # Get all children
            keys = container.keys(tx=tx)

            for key in keys:
                child = container.get_child(key, tx=tx)
                if child is None:
                    continue

                # Recursively extract child value
                child_value = self._extract_value(child, recursive=True)
                if child_value is not None:
                    result[key] = child_value

            # If container is a list type, convert dict to list
            if container.supports_protocol(ContainerProtocol.SEQUENCE):
                # Try to recreate list from dict (assuming integer-like keys)
                try:
                    # Get list length
                    length_key = container._LIST_LENGTH_KEY
                    length_path = container.path.join(length_key)
                    length_node = PrimitiveNode(container.backend, length_path, tx=tx)
                    length = length_node.get_value(tx=tx)

                    if length is not None and not is_empty(length):
                        # Create list with correct length
                        list_result = [None] * int(length)

                        # Fill in values we have
                        for k, v in result.items():
                            try:
                                idx = int(k)
                                if 0 <= idx < len(list_result):
                                    list_result[idx] = v
                            except (ValueError, TypeError):
                                # Skip non-integer keys
                                pass

                        return list_result
                except Exception:
                    # Fall back to dict result on any error
                    pass

        return result

    def _store_value(self, key: PathComponent, value: Any, /) -> Node:
        """
        Store a value at a key, creating appropriate node types.

        Handles different value types (dict, list, set, primitive) and
        creates appropriate container or primitive nodes.

        Args:
            key: Key to store value at
            value: Value to store

        Returns:
            Node: Created or updated node
        """
        with TransactionContext(self.backend, tx=self.tx) as tx:
            # Create child path
            child_path = self.container.path.join(key)
            child_container: Node

            # Handle different value types
            if isinstance(value, dict):
                # Create container with DICT protocol
                child_container = self._ensure_child_container(
                    key, CommonContainerProtocols.DICT, tx=tx
                )

                # Set dictionary values
                for k, v in value.items():
                    # Recursively store values
                    child_container.path.join(k)
                    nested_container = ContainerNode(
                        self.backend,
                        child_container.path,
                        CommonContainerProtocols.DICT,
                        tx=tx,
                    )
                    dict_view = self.__class__(nested_container, tx=tx)
                    dict_view._store_value(k, v)

            elif isinstance(value, (list, tuple)):
                # Create container with LIST protocol
                child_container = self._ensure_child_container(
                    key, CommonContainerProtocols.LIST, tx=tx
                )

                # Import for type hints, not imported at module level to avoid circular imports
                from .list_view import ListView

                # Store list values
                list_view = ListView(child_container, tx=tx)
                list_view.clear()
                for i, item in enumerate(value):
                    list_view.set(i, item)

            elif isinstance(value, set):
                # Create container with SET protocol
                child_container = self._ensure_child_container(
                    key, CommonContainerProtocols.SET, tx=tx
                )

                # Import for type hints, not imported at module level to avoid circular imports
                from .set_view import SetView

                # Store set values
                set_view = SetView(child_container, tx=tx)
                set_view.clear()
                for item in value:
                    set_view.add(item)

            else:
                # Create or update primitive node
                child_container = PrimitiveNode(self.backend, child_path, tx=tx)
                self.container.set_child(key, child_container, tx=tx)
                child_container.set_value(value, tx=tx)

        return child_container

    def _ensure_child_container(
        self,
        key: PathComponent,
        protocols: ContainerProtocol,
        /,
        *,
        tx: Optional[ObservableKVTransaction] = None,
    ) -> ContainerNode:
        """
        Ensure a child container exists with required protocols.

        Args:
            key: Key for child container
            protocols: Required protocols
            tx: Optional transaction

        Returns:
            ContainerNode: Child container with required protocols

        Raises:
            ContainerProtocolError: If container doesn't support mutation
        """
        with TransactionContext(self.backend, tx=tx or self.tx) as tx:
            # Validate container supports mutation
            if not self.container.supports_protocol(ContainerProtocol.MUTABLE):
                raise ContainerProtocolError(
                    f"Container at {self.container.path} does not support mutation"
                )

            # Create child path
            child_path = self.container.path.join(key)

            # Check if child exists and is a container
            child = None
            if self.container.has_child(key, tx=tx):
                child = self.container.get_child(key, tx=tx)

                # If child exists but is not a container, remove it
                if child is not None and child.node_type() != NodeType.CONTAINER:
                    self.container.remove_child(key, tx=tx)
                    child = None

            # Create container if needed
            if child is None:
                # Create container with required protocols
                child = ContainerNode(
                    self.backend,
                    child_path,
                    protocols,
                )

                # Set as child of parent container
                self.container.set_child(key, child, tx=tx)

            # Ensure child has required protocols
            child_container = cast(ContainerNode, child)
            current_protocols = child_container.protocols(tx=tx)

            # Update protocols if needed
            if (current_protocols & protocols) != protocols:
                child_container.update_protocols(current_protocols | protocols, tx=tx)

        return child_container
