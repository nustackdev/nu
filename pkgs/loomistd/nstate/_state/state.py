"""
State implementation for the state management system.

This module defines the State class, which is the primary interface for accessing
and manipulating the state tree. It provides methods for navigation, accessing nodes,
checking types, and creating views.
"""

from __future__ import annotations

import functools
from typing import Any, Callable, TypeVar, cast

from loomi.interfaces.state.observer import SyncSubscriptionProtocol
from loomistd.kv._exceptions import StorageKeyError

from .._core.container import ContainerNode
from .._core.node import Node
from .._core.path import StatePath
from .._core.primitive import PrimitiveNode
from .._exceptions import IncompatibleViewError, PathNotFoundError, PathTypeError
from .._state.backend import (
    ObservableKVBackend,
    ObservableKVTransaction,
    ObservableKVTransactionContextManager,
)
from .._types import (
    CommonContainerProtocols,
    ContainerProtocol,
    NodeType,
    PathComponent,
    StateCallbackFn,
    ViewT,
)
from .._views.dict_view import DictView
from .._views.flat_view import FlatView
from .._views.list_view import ListView
from .._views.set_view import SetView

__all__ = [
    "State",
]

T = TypeVar("T")


def with_state_transaction(method: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for State methods that require transaction handling.

    This decorator ensures that a method executes within a transaction using this priority:
    1. Transaction passed as a keyword argument ('tx')
    2. Transaction stored in the instance (_tx)
    3. Creates a new transaction if neither is available

    For methods that create a new transaction, the decorator handles
    commit/rollback automatically using the backend's transaction context manager.

    Example usage:
    ```python
    @with_state_transaction
    def get(self, *, tx=None):
        # Use tx here for storage operations
        return tx.get(self._path.to_tuple())
    ```

    Args:
        method: The method to decorate

    Returns:
        Decorated method with transaction handling
    """

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        # Extract tx from kwargs if present
        tx = kwargs.pop("tx", None)

        # If no tx in kwargs, use instance tx
        if tx is None:
            tx = self._tx

        # If still no tx, create a new transaction with context manager
        if tx is None:
            # Use backend's transaction context manager
            with self._backend.transaction() as new_tx:
                # Call method with the new transaction
                kwargs["tx"] = new_tx
                return method(self, *args, **kwargs)
        else:
            # Use existing transaction
            kwargs["tx"] = tx
            return method(self, *args, **kwargs)

    return wrapper


class State:
    """
    Primary interface for accessing the state tree.

    State provides methods for navigating the tree, querying and manipulating nodes,
    and creating appropriate views for container nodes. It follows a filesystem-like
    mental model, where containers are like directories and primitives are like files.

    Example:
        ```python
        state = state_service.state

        # Navigation
        users = state.at("users")
        alice = users.at("alice")

        # Checking paths
        if alice.exists():
            print(f"User type: {alice.type()}")

        # Getting and setting values
        name = alice.at("name").get()
        alice.at("email").set("alice@example.com")

        # Using views
        profile = alice.at("profile").dict_view()
        profile.set("location", "San Francisco")

        skills = profile.list_view("skills")
        skills.append("Python")
        ```
    """

    def __init__(
        self,
        backend: ObservableKVBackend,
        path: StatePath | None = None,
        tx: ObservableKVTransaction | None = None,
    ):
        """
        Initialize a State instance.

        Args:
            backend: The backend storage interface
            path: The current path location (default: root)
            tx: Optional transaction for atomic operations
        """
        self._backend = backend
        self._path = path if path is not None else StatePath()
        self._tx = tx

    @property
    def path(self) -> StatePath:
        """
        Get the current path location.

        Returns:
            The current StatePath
        """
        return self._path

    def at(self, *paths: PathComponent) -> State:
        """
        Navigate to a path (relative to current path).

        This creates a new State instance pointing to the specified path.

        Args:
            *paths: Path components to navigate to

        Returns:
            A new State instance for the specified path

        Example:
            ```python
            user = state.at("users", "alice")
            email = state.at("users", "alice", "email")
            ```
        """
        new_path = self._path.join(*paths)
        return State(self._backend, new_path, self._tx)

    @property
    def parent(self) -> State:
        """
        Navigate to parent path.

        Returns:
            A new State instance for the parent path,
            or self if already at root

        Example:
            ```python
            user = state.at("users", "alice")
            users = user.parent
            ```
        """
        parent_path = self._path.parent()
        if parent_path is None:
            # Already at root
            return self
        return State(self._backend, parent_path, self._tx)

    @property
    def root(self) -> State:
        """
        Navigate to root path.

        Returns:
            A new State instance for the root path

        Example:
            ```python
            root = state.at("deeply", "nested", "path").root
            ```
        """
        return State(self._backend, StatePath(), self._tx)

    @with_state_transaction
    def exists(self, *, tx: ObservableKVTransaction) -> bool:
        """
        Check if the current path exists.

        Args:
            tx: Optional transaction to use

        Returns:
            True if the path exists, False otherwise

        Example:
            ```python
            if state.at("users", "alice").exists():
                print("User exists")
            ```
        """
        return tx.exists(self._path.to_tuple())

    @with_state_transaction
    def type(self, *, tx: ObservableKVTransaction) -> NodeType:
        """
        Get the type of node at the current path.

        Args:
            tx: Optional transaction to use

        Returns:
            NodeType.CONTAINER: If path points to a container
            NodeType.PRIMITIVE: If path points to a primitive value
            NodeType.NOT_FOUND: If path doesn't exist

        Example:
            ```python
            if state.at("users").type() == NodeType.CONTAINER:
                # Handle container
            ```
        """
        if not tx.exists(self._path.to_tuple()):
            return NodeType.NOT_FOUND

        node = self._get_node(tx=tx)
        return node.node_type()

    @with_state_transaction
    def protocols(self, *, tx: ObservableKVTransaction) -> ContainerProtocol:
        """
        Get protocols supported by the container at the current path.

        Args:
            tx: Optional transaction to use

        Returns:
            ContainerProtocol flags indicating supported protocols

        Raises:
            PathNotFoundError: If path doesn't exist
            PathTypeError: If path exists but is not a container

        Example:
            ```python
            protocols = state.at("users").protocols()
            if protocols & ContainerProtocol.MAPPING:
                print("Container supports dictionary-like access")
            ```
        """
        if not tx.exists(self._path.to_tuple()):
            raise PathNotFoundError(f"Path {self._path} does not exist")

        node = self._get_node(tx=tx)
        if node.node_type() != NodeType.CONTAINER:
            raise PathTypeError(f"Path {self._path} is not a container")

        return node.protocols()

    @with_state_transaction
    def get(self, *, tx: ObservableKVTransaction) -> Any:
        """
        Get value at the current path.

        Args:
            tx: Optional transaction to use

        For primitive nodes, returns the primitive value.
        For container nodes, returns a nested structure representing the container.

        Returns:
            The value at the current path

        Raises:
            PathNotFoundError: If path doesn't exist

        Example:
            ```python
            user_data = state.at("users", "alice").get()
            ```
        """
        if not tx.exists(self._path.to_tuple()):
            raise PathNotFoundError(f"Path {self._path} does not exist")

        node = self._get_node(tx=tx)
        if node.node_type() == NodeType.PRIMITIVE:
            # Primitive node
            primitive = cast(PrimitiveNode, node)
            return primitive.value
        else:
            # Container node, recursively get all children
            container = cast(ContainerNode, node)
            result = {}

            for key in container.keys():
                child_state = self.at(key)
                result[key] = child_state.get(tx=tx)

            return result

    @with_state_transaction
    def set(self, value: Any, *, tx: ObservableKVTransaction) -> None:
        """
        Set value at the current path.

        Args:
            value: The value to set
            tx: Optional transaction to use

        For primitive values, creates or updates a primitive node.
        For container values (dict, list, etc.), creates or updates a container node.

        Raises:
            PathTypeError: If trying to set primitive at container path or vice versa

        Example:
            ```python
            # Set primitive value
            state.at("users", "alice", "name").set("Alice Smith")

            # Set nested structure
            state.at("users", "alice").set({
                "name": "Alice Smith",
                "email": "alice@example.com"
            })
            ```
        """
        if isinstance(value, dict):
            # Create or update a mapping container
            self._ensure_container(CommonContainerProtocols.DICT, tx=tx)

            # Set all key-value pairs
            for key, val in value.items():
                child_state = self.at(key)
                child_state.set(val, tx=tx)
        elif isinstance(value, (list, tuple, set)):
            # Create or update a sequence container for lists/tuples
            # or a set container for sets
            if isinstance(value, set):
                protocols = CommonContainerProtocols.SET
            else:
                protocols = CommonContainerProtocols.LIST

            self._ensure_container(protocols, tx=tx)

            # For lists/tuples, set index-value pairs
            if isinstance(value, (list, tuple)):
                for i, val in enumerate(value):
                    child_state = self.at(str(i))
                    child_state.set(val, tx=tx)
            else:  # Set
                # Clear existing items
                container_node = cast(ContainerNode, self._get_node(tx=tx))
                if container_node.supports_protocol(ContainerProtocol.MUTABLE):
                    for key in list(container_node.keys()):
                        container_node.remove_child(key)

                # Add new items
                for i, val in enumerate(value):
                    child_state = self.at(str(i))
                    child_state.set(val, tx=tx)
        else:
            # Create or update a primitive node
            if tx.exists(self._path.to_tuple()):
                # Check if it's a container
                type_marker_path = self._path.join(Node._TYPE_KEY)
                if (
                    tx.exists(type_marker_path.to_tuple())
                    and tx.get(type_marker_path.to_tuple()) == "CONTAINER"
                ):
                    raise PathTypeError(
                        f"Cannot set primitive value at container path {self._path}"
                    )

            # Ensure parent paths exist
            parent_path = self._path.parent()
            if parent_path is not None:
                parent_state = State(self._backend, parent_path, tx)
                if not tx.exists(parent_path.to_tuple()):
                    parent_state._ensure_container(CommonContainerProtocols.DICT, tx=tx)

            # Create or update primitive node
            primitive = PrimitiveNode(self._backend, self._path, tx=tx)
            primitive.value = value

    @with_state_transaction
    def remove(self, *, tx: ObservableKVTransaction) -> None:
        """
        Remove the node at the current path and all its children.

        Args:
            tx: Optional transaction to use

        Raises:
            PathNotFoundError: If path doesn't exist

        Example:
            ```python
            state.at("users", "alice").remove()
            ```
        """
        if not tx.exists(self._path.to_tuple()):
            raise PathNotFoundError(f"Path {self._path} does not exist")

        node = self._get_node(tx=tx)
        if node.node_type() == NodeType.CONTAINER:
            # Container node - remove all children first
            container = cast(ContainerNode, node)
            for key in list(container.keys()):
                child_state = self.at(key)
                child_state.remove(tx=tx)

        # Remove the node itself
        tx.delete(self._path.to_tuple())

    def dict_view(self, tx: ObservableKVTransaction) -> DictView:
        """
        Access container as dictionary view.

        If path doesn't exist, creates a new mapping container.
        If path exists but is not a container with MAPPING protocol,
        raises an error.

        Args:
            tx: Optional transaction (defaults to current transaction)

        Returns:
            DictView for the container

        Raises:
            IncompatibleViewError: If container doesn't support MAPPING protocol

        Example:
            ```python
            users = state.at("users").dict_view()
            users.set("alice", {"email": "alice@example.com"})
            ```
        """
        # Use transaction from args or instance
        tx = tx or self._tx

        # Ensure container exists and supports MAPPING protocol
        container = self._ensure_container(CommonContainerProtocols.DICT, tx=tx)
        if not container.supports_protocol(ContainerProtocol.MAPPING):
            raise IncompatibleViewError(
                f"Container at {self._path} does not support the MAPPING protocol"
            )

        # Create DictView for the container
        return DictView(self._backend, self._path, tx)

    def list_view(self, tx: ObservableKVTransaction) -> ListView:
        """
        Access container as list view.

        If path doesn't exist, creates a new sequence container.
        If path exists but is not a container with SEQUENCE protocol,
        raises an error.

        Args:
            tx: Optional transaction (defaults to current transaction)

        Returns:
            ListView for the container

        Raises:
            IncompatibleViewError: If container doesn't support SEQUENCE protocol

        Example:
            ```python
            tasks = state.at("tasks").list_view()
            tasks.append("Buy groceries")
            ```
        """
        # Use transaction from args or instance
        tx = tx or self._tx

        # Ensure container exists and supports SEQUENCE protocol
        container = self._ensure_container(CommonContainerProtocols.LIST, tx=tx)
        if not container.supports_protocol(ContainerProtocol.SEQUENCE):
            raise IncompatibleViewError(
                f"Container at {self._path} does not support the SEQUENCE protocol"
            )

        # Create ListView for the container
        return ListView(self._backend, self._path, tx)

    def set_view(self, tx: ObservableKVTransaction) -> SetView:
        """
        Access container as set view.

        If path doesn't exist, creates a new set container.
        If path exists but is not a container with SET protocol,
        raises an error.

        Args:
            tx: Optional transaction (defaults to current transaction)

        Returns:
            SetView for the container

        Raises:
            IncompatibleViewError: If container doesn't support SET protocol

        Example:
            ```python
            tags = state.at("tags").set_view()
            tags.add("important")
            ```
        """
        # Use transaction from args or instance
        tx = tx or self._tx

        # Ensure container exists and supports SET protocol
        container = self._ensure_container(CommonContainerProtocols.SET, tx=tx)
        if not container.supports_protocol(ContainerProtocol.SET):
            raise IncompatibleViewError(
                f"Container at {self._path} does not support the SET protocol"
            )

        # Create SetView for the container
        return SetView(self._backend, self._path, tx)

    def flat_view(self, tx: ObservableKVTransaction) -> FlatView:
        """
        Access container as flat view.

        If path doesn't exist, creates a new flat mapping container.
        If path exists but is not a container with MAPPING and FLAT protocols,
        raises an error.

        Args:
            tx: Optional transaction (defaults to current transaction)

        Returns:
            FlatView for the container

        Raises:
            IncompatibleViewError: If container doesn't support required protocols

        Example:
            ```python
            config = state.at("config").flat_view()
            config.set("theme", "dark")
            ```
        """
        # Use transaction from args or instance
        tx = tx or self._tx

        # Ensure container exists and supports MAPPING and FLAT protocols
        container = self._ensure_container(CommonContainerProtocols.FLAT_DICT, tx=tx)
        if not (
            container.supports_protocol(ContainerProtocol.MAPPING)
            and container.supports_protocol(ContainerProtocol.FLAT)
        ):
            raise IncompatibleViewError(
                f"Container at {self._path} does not support the MAPPING and FLAT protocols"
            )

        # Create FlatView for the container
        return FlatView(self._backend, self._path, tx)

    def view(self, view_class: type[ViewT], tx: ObservableKVTransaction) -> ViewT:
        """
        Access container via custom view class.

        If path doesn't exist, creates a new container with protocols
        required by the view class.
        If path exists but doesn't support required protocols, raises an error.

        Args:
            view_class: The view class to use
            tx: Optional transaction (defaults to current transaction)

        Returns:
            Instance of the specified view class

        Raises:
            IncompatibleViewError: If container doesn't support required protocols

        Example:
            ```python
            custom_view = state.at("custom").view(CustomView)
            ```
        """
        # Use transaction from args or instance
        tx = tx or self._tx

        # Get required protocols from view class
        required_protocols = getattr(
            view_class, "required_protocols", lambda: ContainerProtocol.CONTAINER
        )()

        # Ensure container exists and supports required protocols
        container = self._ensure_container(required_protocols, tx=tx)
        for protocol in [p for p in ContainerProtocol if p & required_protocols]:
            if not container.supports_protocol(protocol):
                raise IncompatibleViewError(
                    f"Container at {self._path} does not support required protocol {protocol}"
                )

        # Create view instance
        return view_class(self._backend, self._path, tx)

    def begin_transaction(self) -> ObservableKVTransaction:
        """
        Start a new transaction.

        Returns:
            New transaction object

        Example:
            ```python
            tx = state.begin_transaction()
            try:
                # Perform operations with tx
                state.commit(tx)
            except Exception:
                state.rollback(tx)
            ```
        """
        return self._backend.begin_transaction()

    def transaction(self) -> ObservableKVTransactionContextManager:
        """
        Get a transaction context manager.

        Returns:
            Transaction context manager

        Example:
            ```python
            with state.transaction() as tx:
                # Perform operations with tx
                # Auto-commits on success, auto-rollbacks on exception
            ```
        """
        return self._backend.transaction()

    def subscribe(self, callback: StateCallbackFn, depth: int = 0) -> SyncSubscriptionProtocol:
        """
        Subscribe to changes at the current path.

        Args:
            callback: Function to call when changes occur
            depth: Depth of topic pattern matching (default: 0 for exact match)
                If set to 0, matches exact topic; if set to 1, matches prefix; if set to -1, matches all subtopics.

        Returns:
            Subscription object for unsubscribing

        Example:
            ```python
            def on_change(path):
                print(f"Path {path} changed")

            sub = state.at("users").subscribe(on_change)
            # Later, unsubscribe
            sub.unsubscribe()
            ```
        """
        return self._backend.subscribe(self._path.to_tuple(), callback, depth)

    @with_state_transaction
    def _get_node(self, *, tx: ObservableKVTransaction) -> Node:
        """
        Get the node at the current path.

        Args:
            tx: Optional transaction to use

        Returns:
            Node object (ContainerNode or PrimitiveNode)

        Raises:
            PathNotFoundError: If path doesn't exist
        """
        if not tx.exists(self._path.to_tuple()):
            raise PathNotFoundError(f"Path {self._path} does not exist")

        # Check if it's a container by checking for a type marker
        type_marker_path = self._path.join(Node._TYPE_KEY)
        if tx.exists(type_marker_path.to_tuple()):
            # It's a container, get its protocols
            type_value = tx.get(type_marker_path.to_tuple())
            if type_value == "CONTAINER":
                protocols_path = self._path.join(Node._PROTOCOLS_KEY)
                try:
                    protocols_value = tx.get(protocols_path.to_tuple())
                    protocols = ContainerProtocol(protocols_value)
                except (StorageKeyError, ValueError):
                    # Default to basic container if protocols not found
                    protocols = ContainerProtocol.CONTAINER

                return ContainerNode(self._backend, self._path, protocols, tx=tx)

        # No type marker or not a container, treat as primitive
        return PrimitiveNode(self._backend, self._path, tx=tx)

    @with_state_transaction
    def _ensure_container(
        self, protocols: ContainerProtocol, *, tx: ObservableKVTransaction
    ) -> ContainerNode:
        """
        Ensure a container node exists at the current path with specified protocols.

        Args:
            protocols: The protocols the container should support
            tx: Optional transaction to use

        If path exists and is a container, validates it supports the protocols.
        If path doesn't exist, creates parent paths and a container node.

        Returns:
            ContainerNode at the current path

        Raises:
            PathTypeError: If path exists but is not a container
            ContainerProtocolError: If container exists but doesn't support required protocols
        """
        if tx.exists(self._path.to_tuple()):
            # Check if it's a container
            type_marker_path = self._path.join(Node._TYPE_KEY)
            if (
                not tx.exists(type_marker_path.to_tuple())
                or tx.get(type_marker_path.to_tuple()) != "CONTAINER"
            ):
                raise PathTypeError(f"Path {self._path} exists but is not a container")

            # Path exists and is a container, get the node
            container = ContainerNode(self._backend, self._path, protocols, tx=tx)

            # Validate it supports the specified protocols
            # (If not, we could potentially update its protocols here)
            return container
        else:
            # Path doesn't exist, ensure parent paths exist
            parent_path = self._path.parent()
            if parent_path is not None:
                parent_state = State(self._backend, parent_path, tx)
                if not tx.exists(parent_path.to_tuple()):
                    # Create parent path with default dict protocol
                    parent_state._ensure_container(CommonContainerProtocols.DICT, tx=tx)

            # Create container node at path
            container = ContainerNode(self._backend, self._path, protocols, tx=tx)
            return container
