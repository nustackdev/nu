"""
DictView implementation for the state management system.

This module defines the DictView class, which provides a dictionary-like
interface for containers implementing the MAPPING protocol.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, TypeVar, cast

from .._core.container import ContainerNode
from .._core.path import StatePath
from .._core.primitive import PrimitiveNode
from .._exceptions import IncompatibleViewError, PathNotFoundError, PathTypeError
from .._state.backend import ObservableKVBackend, ObservableKVTransaction
from .._types import CommonContainerProtocols, ContainerProtocol, NodeType, PathComponent

# Forward references for other view types
if TYPE_CHECKING:
    from .flat_view import FlatView
    from .list_view import ListView
    from .set_view import SetView

ViewT = TypeVar("ViewT")


class DictView:
    """
    Dictionary view for containers implementing the MAPPING protocol.

    DictView provides a dictionary-like interface for interacting with
    containers, allowing key-based access and modification of child nodes.
    It supports standard dictionary operations like get, set, keys, values,
    items, as well as nested container access.

    Example:
        ```python
        # Access a container as a dictionary
        users = state.at("users").dict_view()

        # Set values
        users.set("alice", {"email": "alice@example.com"})
        users.set("bob", {"email": "bob@example.com"})

        # Get values
        alice_email = users.get("alice").get("email")

        # Access nested containers
        alice = users.dict_view("alice")
        alice.set("location", "San Francisco")
        ```
    """

    # Define the required protocols for this view
    @staticmethod
    def required_protocols() -> ContainerProtocol:
        """
        Get the protocols required by this view.

        Returns:
            ContainerProtocol flags indicating required protocols
        """
        return ContainerProtocol.MAPPING

    def __init__(
        self,
        backend: ObservableKVBackend,
        path: StatePath,
        tx: Optional[ObservableKVTransaction] = None,
    ):
        """
        Initialize a dictionary view.

        Args:
            backend: The backend storage interface
            path: Path to the container
            tx: Optional transaction for atomic operations

        Raises:
            IncompatibleViewError: If container doesn't support MAPPING protocol
        """
        self._backend = backend
        self._path = path
        self._tx = tx

        # Validate container supports MAPPING protocol
        with self._transaction() as tx:
            container = self._get_container_node(tx)
            if not container.supports_protocol(ContainerProtocol.MAPPING):
                raise IncompatibleViewError(
                    f"Container at {path} does not support the MAPPING protocol"
                )

    @property
    def path(self) -> StatePath:
        """
        Get the current path location.

        Returns:
            The current StatePath
        """
        return self._path

    def at(self, *paths: PathComponent) -> "StatePath":
        """
        Navigate to a path (relative to current path).

        Args:
            *paths: Path components to navigate to

        Returns:
            A new StatePath for the specified path
        """
        return self._path.join(*paths)

    @property
    def parent(self) -> StatePath:
        """
        Get the parent path.

        Returns:
            The parent StatePath, or self._path if already at root
        """
        parent = self._path.parent()
        return parent if parent is not None else self._path

    def exists(self) -> bool:
        """
        Check if the current path exists.

        Returns:
            True if the path exists, False otherwise
        """
        with self._transaction() as tx:
            return tx.exists(self._path.to_tuple())

    def type(self) -> NodeType:
        """
        Get the type of node at the current path.

        Returns:
            NodeType.CONTAINER, NodeType.PRIMITIVE, or NodeType.NOT_FOUND
        """
        with self._transaction() as tx:
            if not tx.exists(self._path.to_tuple()):
                return NodeType.NOT_FOUND

            container = self._get_container_node(tx)
            return container.node_type()

    def protocols(self) -> ContainerProtocol:
        """
        Get protocols supported by the container at the current path.

        Returns:
            ContainerProtocol flags indicating supported protocols

        Raises:
            PathNotFoundError: If path doesn't exist
            PathTypeError: If path exists but is not a container
        """
        with self._transaction() as tx:
            container = self._get_container_node(tx)
            return container.protocols()

    def get(self, key: PathComponent) -> Any:
        """
        Get the value associated with the key.

        Args:
            key: The key to retrieve

        Returns:
            The value associated with the key, or None if the key doesn't exist

        Example:
            ```python
            name = users.get("alice")
            ```
        """
        with self._transaction() as tx:
            container = self._get_container_node(tx)

            if not container.has_child(key, tx=tx):
                return None

            child = container.get_child(key, tx=tx)

            if child is None:
                return None

            if child.node_type() == NodeType.PRIMITIVE:
                primitive = cast(PrimitiveNode, child)
                return primitive.get_value(tx=tx)
            else:
                # For container nodes, recursively get all children
                container_child = cast(ContainerNode, child)
                result = {}

                for child_key in container_child.keys(tx=tx):
                    grand_child = container_child.get_child(child_key, tx=tx)
                    if grand_child is None:
                        continue

                    if grand_child.node_type() == NodeType.PRIMITIVE:
                        primitive_grand_child = cast(PrimitiveNode, grand_child)
                        result[child_key] = primitive_grand_child.get_value(tx=tx)
                    else:
                        # Simplify by just indicating it's a container
                        result[child_key] = {}

                return result

    def set(self, key: PathComponent, value: Any) -> None:
        """
        Set a key-value pair.

        Args:
            key: The key to set
            value: The value to associate with the key

        Example:
            ```python
            users.set("alice", {"email": "alice@example.com"})
            ```
        """
        with self._transaction() as tx:
            container = self._get_container_node(tx)

            if isinstance(value, dict):
                # Create a container node for the dictionary
                child_path = self._path.join(key)
                child_container = ContainerNode(
                    self._backend, child_path, CommonContainerProtocols.DICT, tx=tx
                )
                container.set_child(key, child_container, tx=tx)

                # Set all key-value pairs in the dictionary
                for k, v in value.items():
                    child_dict_view = self.dict_view(key, tx=tx)
                    child_dict_view.set(k, v)

            elif isinstance(value, (list, tuple, set)):
                # Create appropriate container for the collection
                child_path = self._path.join(key)
                if isinstance(value, set):
                    protocols = CommonContainerProtocols.SET
                else:
                    protocols = CommonContainerProtocols.LIST

                child_container = ContainerNode(self._backend, child_path, protocols, tx=tx)
                container.set_child(key, child_container, tx=tx)

                # Handle collections with subview (to be implemented)
                # For now, just store as primitives with string indices
                if isinstance(value, (list, tuple)):
                    child_view = self.dict_view(key, tx=tx)
                    for i, v in enumerate(value):
                        child_view.set(str(i), v)
                else:  # Set
                    child_view = self.dict_view(key, tx=tx)
                    for i, v in enumerate(value):
                        child_view.set(str(i), v)

            else:
                # Create a primitive node for the value
                child_path = self._path.join(key)
                child_node = PrimitiveNode(self._backend, child_path, tx=tx)
                child_node.set_value(value, tx=tx)
                container.set_child(key, child_node, tx=tx)

    def has(self, key: PathComponent) -> bool:
        """
        Check if a key exists.

        Args:
            key: The key to check

        Returns:
            True if the key exists, False otherwise

        Example:
            ```python
            if users.has("alice"):
                print("User Alice exists")
            ```
        """
        with self._transaction() as tx:
            container = self._get_container_node(tx)
            return container.has_child(key, tx=tx)

    def remove(self, key: PathComponent) -> None:
        """
        Remove a key and its associated value.

        Args:
            key: The key to remove

        Raises:
            PathNotFoundError: If the key doesn't exist

        Example:
            ```python
            users.remove("alice")
            ```
        """
        with self._transaction() as tx:
            container = self._get_container_node(tx)

            if not container.has_child(key, tx=tx):
                raise PathNotFoundError(f"Key '{key}' does not exist at {self._path}")

            container.remove_child(key, tx=tx)

    def update(self, mapping: Dict[PathComponent, Any]) -> None:
        """
        Update the dictionary with multiple key-value pairs.

        Args:
            mapping: Dictionary of key-value pairs to update

        Example:
            ```python
            users.update({
                "alice": {"email": "alice@example.com"},
                "bob": {"email": "bob@example.com"}
            })
            ```
        """
        with self._transaction() as tx:
            for key, value in mapping.items():
                self.set(key, value)

    def keys(self) -> List[PathComponent]:
        """
        Get all keys in the dictionary.

        Returns:
            A list of all keys

        Example:
            ```python
            user_ids = users.keys()
            ```
        """
        with self._transaction() as tx:
            container = self._get_container_node(tx)
            return container.keys(tx=tx)

    def values(self) -> List[Any]:
        """
        Get all values in the dictionary.

        Returns:
            A list of all values

        Example:
            ```python
            user_data = users.values()
            ```
        """
        result = []
        for key in self.keys():
            result.append(self.get(key))
        return result

    def items(self) -> List[Tuple[PathComponent, Any]]:
        """
        Get all key-value pairs in the dictionary.

        Returns:
            A list of (key, value) tuples

        Example:
            ```python
            for key, value in users.items():
                print(f"{key}: {value}")
            ```
        """
        result = []
        for key in self.keys():
            result.append((key, self.get(key)))
        return result

    def dict_view(
        self, key: PathComponent, tx: Optional[ObservableKVTransaction] = None
    ) -> "DictView":
        """
        Get a dictionary view for a child container.

        Args:
            key: The key of the child container
            tx: Optional transaction to use

        Returns:
            DictView for the child container

        Example:
            ```python
            alice = users.dict_view("alice")
            alice.set("email", "alice@example.com")
            ```
        """
        child_path = self._path.join(key)

        # Use transaction from args or instance or create a new one
        transaction = tx or self._tx

        with self._transaction(transaction) as tx:
            container = self._get_container_node(tx)

            # Check if child exists
            if not container.has_child(key, tx=tx):
                # Create new container with DICT protocol
                child_container = ContainerNode(
                    self._backend, child_path, CommonContainerProtocols.DICT, tx=tx
                )
                container.set_child(key, child_container, tx=tx)
            else:
                # Get existing child and ensure it's a container
                child = container.get_child(key, tx=tx)
                if child is None or child.node_type() != NodeType.CONTAINER:
                    # Replace with container
                    child_container = ContainerNode(
                        self._backend, child_path, CommonContainerProtocols.DICT, tx=tx
                    )
                    container.set_child(key, child_container, tx=tx)

        # Create new view with the provided transaction (or self._tx if None)
        return DictView(self._backend, child_path, tx or self._tx)

    def list_view(
        self, key: PathComponent, tx: Optional[ObservableKVTransaction] = None
    ) -> "ListView":
        """
        Get a list view for a child container.

        Args:
            key: The key of the child container
            tx: Optional transaction to use

        Returns:
            ListView for the child container

        Example:
            ```python
            skills = profile.list_view("skills")
            skills.append("Python")
            ```
        """
        from .list_view import ListView

        child_path = self._path.join(key)

        # Use transaction from args or instance or create a new one
        transaction = tx or self._tx

        with self._transaction(transaction) as tx:
            container = self._get_container_node(tx)

            # Check if child exists
            if not container.has_child(key, tx=tx):
                # Create new container with LIST protocol
                child_container = ContainerNode(
                    self._backend, child_path, CommonContainerProtocols.LIST, tx=tx
                )
                container.set_child(key, child_container, tx=tx)
            else:
                # Get existing child and ensure it's a container with LIST protocol
                child = container.get_child(key, tx=tx)
                if child is None or child.node_type() != NodeType.CONTAINER:
                    # Replace with container
                    child_container = ContainerNode(
                        self._backend, child_path, CommonContainerProtocols.LIST, tx=tx
                    )
                    container.set_child(key, child_container, tx=tx)
                elif child.node_type() == NodeType.CONTAINER and not child.supports_protocol(
                    ContainerProtocol.SEQUENCE
                ):
                    # It's a container but not a list, raise error
                    raise IncompatibleViewError(
                        f"Container at {child_path} does not support the SEQUENCE protocol"
                    )

        # Create new view with the provided transaction (or self._tx if None)
        return ListView(self._backend, child_path, tx or self._tx)

    def set_view(
        self, key: PathComponent, tx: Optional[ObservableKVTransaction] = None
    ) -> "SetView":
        """
        Get a set view for a child container.

        Args:
            key: The key of the child container
            tx: Optional transaction to use

        Returns:
            SetView for the child container

        Example:
            ```python
            tags = profile.set_view("tags")
            tags.add("important")
            ```
        """
        from .set_view import SetView

        child_path = self._path.join(key)

        # Use transaction from args or instance or create a new one
        transaction = tx or self._tx

        with self._transaction(transaction) as tx:
            container = self._get_container_node(tx)

            # Check if child exists
            if not container.has_child(key, tx=tx):
                # Create new container with SET protocol
                child_container = ContainerNode(
                    self._backend, child_path, CommonContainerProtocols.SET, tx=tx
                )
                container.set_child(key, child_container, tx=tx)
            else:
                # Get existing child and ensure it's a container with SET protocol
                child = container.get_child(key, tx=tx)
                if child is None or child.node_type() != NodeType.CONTAINER:
                    # Replace with container
                    child_container = ContainerNode(
                        self._backend, child_path, CommonContainerProtocols.SET, tx=tx
                    )
                    container.set_child(key, child_container, tx=tx)
                elif child.node_type() == NodeType.CONTAINER and not child.supports_protocol(
                    ContainerProtocol.SET
                ):
                    # It's a container but not a set, raise error
                    raise IncompatibleViewError(
                        f"Container at {child_path} does not support the SET protocol"
                    )

        # Create new view with the provided transaction (or self._tx if None)
        return SetView(self._backend, child_path, tx or self._tx)

    def flat_view(
        self, key: PathComponent, tx: Optional[ObservableKVTransaction] = None
    ) -> "FlatView":
        """
        Get a flat view for a child container.

        Args:
            key: The key of the child container
            tx: Optional transaction to use

        Returns:
            FlatView for the child container

        Example:
            ```python
            settings = profile.flat_view("settings")
            settings.set("theme", "dark")
            ```
        """
        from .flat_view import FlatView

        child_path = self._path.join(key)

        # Use transaction from args or instance or create a new one
        transaction = tx or self._tx

        with self._transaction(transaction) as tx:
            container = self._get_container_node(tx)

            # Check if child exists
            if not container.has_child(key, tx=tx):
                # Create new container with FLAT_DICT protocol
                child_container = ContainerNode(
                    self._backend, child_path, CommonContainerProtocols.FLAT_DICT, tx=tx
                )
                container.set_child(key, child_container, tx=tx)
            else:
                # Get existing child and ensure it's a container with FLAT_DICT protocol
                child = container.get_child(key, tx=tx)
                if child is None or child.node_type() != NodeType.CONTAINER:
                    # Replace with container
                    child_container = ContainerNode(
                        self._backend, child_path, CommonContainerProtocols.FLAT_DICT, tx=tx
                    )
                    container.set_child(key, child_container, tx=tx)
                elif child.node_type() == NodeType.CONTAINER and not (
                    child.supports_protocol(ContainerProtocol.MAPPING)
                    and child.supports_protocol(ContainerProtocol.FLAT)
                ):
                    # It's a container but not flat, raise error
                    raise IncompatibleViewError(
                        f"Container at {child_path} does not support the MAPPING and FLAT protocols"
                    )

        # Create new view with the provided transaction (or self._tx if None)
        return FlatView(self._backend, child_path, tx or self._tx)

    def view(
        self,
        key: PathComponent,
        view_class: type[ViewT],
        tx: Optional[ObservableKVTransaction] = None,
    ) -> ViewT:
        """
        Get a custom view for a child container.

        Args:
            key: The key of the child container
            view_class: The view class to use
            tx: Optional transaction to use

        Returns:
            Instance of the specified view class

        Example:
            ```python
            custom_view = users.view("alice", CustomView)
            ```
        """
        child_path = self._path.join(key)

        # Use transaction from args or instance or create a new one
        transaction = tx or self._tx

        # Get required protocols from view class
        required_protocols = getattr(
            view_class, "required_protocols", lambda: ContainerProtocol.CONTAINER
        )()

        with self._transaction(transaction) as tx:
            container = self._get_container_node(tx)

            # Check if child exists
            if not container.has_child(key, tx=tx):
                # Create new container with required protocols
                child_container = ContainerNode(
                    self._backend, child_path, required_protocols, tx=tx
                )
                container.set_child(key, child_container, tx=tx)
            else:
                # Get existing child and ensure it supports required protocols
                child = container.get_child(key, tx=tx)
                if child is None or child.node_type() != NodeType.CONTAINER:
                    # Replace with container
                    child_container = ContainerNode(
                        self._backend, child_path, required_protocols, tx=tx
                    )
                    container.set_child(key, child_container, tx=tx)
                elif child.node_type() == NodeType.CONTAINER:
                    # Check required protocols
                    for protocol in [p for p in ContainerProtocol if p & required_protocols]:
                        if not child.supports_protocol(protocol):
                            raise IncompatibleViewError(
                                f"Container at {child_path} does not support required protocol {protocol}"
                            )

        # Create new view with the provided transaction (or self._tx if None)
        return view_class(self._backend, child_path, tx or self._tx)

    def to_dict(self) -> Dict[PathComponent, Any]:
        """
        Convert the view to a Python dictionary.

        Returns:
            A dictionary representation of the container

        Example:
            ```python
            user_dict = users.to_dict()
            ```
        """
        result = {}
        for key, value in self.items():
            result[key] = value
        return result

    def _get_container_node(self, tx: ObservableKVTransaction) -> ContainerNode:
        """
        Get the container node at the current path.

        Args:
            tx: Transaction to use

        Returns:
            ContainerNode at the current path

        Raises:
            PathNotFoundError: If path doesn't exist
            PathTypeError: If path exists but is not a container
        """
        if not tx.exists(self._path.to_tuple()):
            raise PathNotFoundError(f"Path {self._path} does not exist")

        # Check if it's a container by checking for a type marker
        type_marker_path = self._path.join(ContainerNode._TYPE_KEY)
        if (
            not tx.exists(type_marker_path.to_tuple())
            or tx.get(type_marker_path.to_tuple()) != "CONTAINER"
        ):
            raise PathTypeError(f"Path {self._path} exists but is not a container")

        # Get container protocols
        protocols_path = self._path.join(ContainerNode._PROTOCOLS_KEY)
        try:
            protocols_value = tx.get(protocols_path.to_tuple())
            protocols = ContainerProtocol(protocols_value)
        except Exception:
            # Default to basic container if protocols not found
            protocols = ContainerProtocol.CONTAINER

        return ContainerNode(self._backend, self._path, protocols, tx=tx)

    def _transaction(self, tx: Optional[ObservableKVTransaction] = None):
        """
        Get a transaction context manager.

        Args:
            tx: Optional existing transaction to use

        Returns:
            Transaction context manager

        This method handles transaction priority:
        1. Use the provided transaction if not None
        2. Use self._tx if not None
        3. Create a new transaction if both are None

        For the case where a new transaction is created, the context manager
        handles commit/rollback automatically.
        """
        if tx is not None:
            # Use provided transaction (no context manager needed)
            class NoopContextManager:
                def __enter__(self):
                    return tx

                def __exit__(self, exc_type, exc_val, exc_tb):
                    return False

            return NoopContextManager()
        elif self._tx is not None:
            # Use instance transaction (no context manager needed)
            class NoopContextManager:
                def __enter__(self):
                    return self._tx

                def __exit__(self, exc_type, exc_val, exc_tb):
                    return False

            return NoopContextManager()
        else:
            # Create new transaction with context manager
            return self._backend.transaction()
