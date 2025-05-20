"""
DictView implementation for the state management system.

This module defines the DictView class, which provides a dictionary-like
interface for containers implementing the MAPPING protocol.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, TypeVar, cast

from .._core.container import ContainerNode
from .._core.primitive import PrimitiveNode
from .._state.backend import ObservableKVTransaction
from .._types import CommonContainerProtocols, ContainerProtocol, NodeType, PathComponent
from .._utils import is_empty
from .view import BaseView

if TYPE_CHECKING:
    from .flat_view import FlatView
    from .list_view import ListView
    from .set_view import SetView

ViewT = TypeVar("ViewT", bound=BaseView)

__all__ = ["DictView"]


class DictView(BaseView):
    """
    Dictionary view for containers implementing the MAPPING protocol.

    DictView provides a dictionary-like interface for interacting with
    containers, allowing key-based access and modification of child nodes.
    It supports standard dictionary operations like get, set, keys, values,
    items, as well as nested container access through other views.

    Example:
        ```python
        # Create a dictionary view
        users = state.at("users").dict_view()

        # Set and get values
        users.set("alice", {"email": "alice@example.com"})
        alice_email = users.get("alice").get("email")

        # Check for keys
        if users.has("bob"):
            print("Bob exists")

        # Iterate over items
        for username, user_data in users.items():
            print(f"{username}: {user_data}")
        ```
    """

    @staticmethod
    def required_protocols() -> ContainerProtocol:
        """
        Get the protocols required by this view.

        Returns:
            ContainerProtocol: MAPPING protocol
        """
        return ContainerProtocol.MAPPING

    def get(self, key: PathComponent, /) -> Any:
        """
        Get the value associated with a key.

        Args:
            key: Key to get value for

        Returns:
            Any: Value associated with key, or None if key doesn't exist

        Example:
            ```python
            user_data = users.get("alice")
            ```
        """
        # Check if child exists
        if not self.container.has_child(key, tx=self._tx):
            return None

        # Get child node
        child = self.container.get_child(key, tx=self._tx)
        if child is None:
            return None

        # Handle primitive nodes
        if child.node_type() == NodeType.PRIMITIVE:
            primitive = cast(PrimitiveNode, child)
            value = primitive.get_value(tx=self._tx)
            return None if is_empty(value) else value

        # Handle container nodes (recursively get values)
        child_container = cast(ContainerNode, child)
        return self._extract_container_value(child_container)

    def _extract_container_value(self, container: ContainerNode) -> Any:
        """
        Extract a value from a container node.

        Recursively extracts values from a container by creating a dictionary
        representation of its children.

        Args:
            container: Container node to extract value from

        Returns:
            Any: Dictionary representation of the container's children
        """
        result = {}

        # Get all child keys
        for key in container.keys(tx=self._tx):
            child = container.get_child(key, tx=self._tx)
            if child is None:
                continue

            if child.node_type() == NodeType.PRIMITIVE:
                # Extract primitive value
                primitive = cast(PrimitiveNode, child)
                value = primitive.get_value(tx=self._tx)
                if not is_empty(value):
                    result[key] = value
            else:
                # Recursively extract container value
                child_container = cast(ContainerNode, child)
                result[key] = self._extract_container_value(child_container)

        return result

    def set(self, key: PathComponent, value: Any, /) -> None:
        """
        Set a value for a key.

        Args:
            key: Key to set value for
            value: Value to associate with key

        Raises:
            ContainerProtocolError: If container doesn't support mutation

        Example:
            ```python
            users.set("alice", {"name": "Alice Smith", "email": "alice@example.com"})
            ```
        """
        # Create child path
        child_path = self.container.path.join(key)

        # Handle different value types
        if isinstance(value, dict):
            # Create a container node with DICT protocol
            child_container = ContainerNode(
                self.container.backend, child_path, CommonContainerProtocols.DICT, tx=self._tx
            )

            # Set the container as child
            self.container.set_child(key, child_container, tx=self._tx)

            # Set all key-value pairs in the dictionary
            for k, v in value.items():
                # Create a DictView for the child container
                child_view = DictView(child_container, tx=self._tx)
                child_view.set(k, v)

        elif isinstance(value, (list, tuple)):
            # Create a container node with LIST protocol
            child_container = ContainerNode(
                self.container.backend, child_path, CommonContainerProtocols.LIST, tx=self._tx
            )

            # Set the container as child
            self.container.set_child(key, child_container, tx=self._tx)

            # Import here to avoid circular imports
            from .list_view import ListView

            # Set all items in the list
            list_view = ListView(child_container, tx=self._tx)
            for i, item in enumerate(value):
                list_view.set(i, item)

        elif isinstance(value, set):
            # Create a container node with SET protocol
            child_container = ContainerNode(
                self.container.backend, child_path, CommonContainerProtocols.SET, tx=self._tx
            )

            # Set the container as child
            self.container.set_child(key, child_container, tx=self._tx)

            # Import here to avoid circular imports
            from .set_view import SetView

            # Set all items in the set
            set_view = SetView(child_container, tx=self._tx)
            for item in value:
                set_view.add(item)

        else:
            # Create a primitive node for the value
            primitive = PrimitiveNode(self.container.backend, child_path, tx=self._tx)

            # Set the value and add the primitive to the container
            primitive.set_value(value, tx=self._tx)
            self.container.set_child(key, primitive, tx=self._tx)

    def has(self, key: PathComponent, /) -> bool:
        """
        Check if a key exists.

        Args:
            key: Key to check

        Returns:
            bool: True if key exists

        Example:
            ```python
            if users.has("alice"):
                print("User Alice exists")
            ```
        """
        return self.container.has_child(key, tx=self._tx)

    def remove(self, key: PathComponent, /) -> None:
        """
        Remove a key and its associated value.

        Args:
            key: Key to remove

        Raises:
            KeyError: If key doesn't exist
            ContainerProtocolError: If container doesn't support mutation

        Example:
            ```python
            users.remove("alice")
            ```
        """
        self.container.remove_child(key, tx=self._tx)

    def update(self, mapping: Dict[PathComponent, Any], /) -> None:
        """
        Update multiple key-value pairs.

        Args:
            mapping: Dictionary of key-value pairs to update

        Raises:
            ContainerProtocolError: If container doesn't support mutation

        Example:
            ```python
            users.update({
                "alice": {"email": "alice@example.com"},
                "bob": {"email": "bob@example.com"}
            })
            ```
        """
        for key, value in mapping.items():
            self.set(key, value)

    def values(self) -> List[Any]:
        """
        Get all values in the dictionary.

        Returns:
            List[Any]: List of values

        Example:
            ```python
            user_data_list = users.values()
            ```
        """
        result = []
        for key in self.keys():
            value = self.get(key)
            if value is not None:
                result.append(value)
        return result

    def items(self) -> List[Tuple[PathComponent, Any]]:
        """
        Get all key-value pairs.

        Returns:
            List[Tuple[PathComponent, Any]]: List of (key, value) tuples

        Example:
            ```python
            for username, user_data in users.items():
                print(f"{username}: {user_data}")
            ```
        """
        result = []
        for key in self.keys():
            value = self.get(key)
            if value is not None:
                result.append((key, value))
        return result

    def clear(self) -> None:
        """
        Remove all key-value pairs.

        Raises:
            ContainerProtocolError: If container doesn't support mutation

        Example:
            ```python
            users.clear()
            ```
        """
        self.container.clear(tx=self._tx)

    def dict_view(
        self, key: PathComponent, /, *, tx: Optional[ObservableKVTransaction] = None
    ) -> DictView:
        """
        Get a dictionary view for a child container.

        Creates the child container if it doesn't exist.

        Args:
            key: Key of child container
            tx: Optional transaction

        Returns:
            DictView: Dictionary view for child container

        Example:
            ```python
            # Access nested dictionary
            alice = users.dict_view("alice")
            alice.set("name", "Alice Smith")
            ```
        """
        transaction = tx or self._tx

        # Create child path
        child_path = self.container.path.join(key)

        # Check if child exists and is a container
        child = None
        if self.container.has_child(key, tx=transaction):
            child = self.container.get_child(key, tx=transaction)

            # If child exists but is not a container, remove it
            if child is not None and child.node_type() != NodeType.CONTAINER:
                self.container.remove_child(key, tx=transaction)
                child = None

        # Create container if needed
        if child is None:
            # Create a container with DICT protocols
            child = ContainerNode(
                self.container.backend,
                child_path,
                CommonContainerProtocols.DICT,
                tx=transaction,
            )

            # Set as child
            self.container.set_child(key, child, tx=transaction)

        # Ensure child has required protocols
        child_container = cast(ContainerNode, child)
        current_protocols = child_container.protocols(tx=transaction)
        required_protocols = CommonContainerProtocols.DICT

        # Update protocols if needed
        if (current_protocols & required_protocols) != required_protocols:
            child_container.update_protocols(current_protocols | required_protocols, tx=transaction)

        # Return view for child container
        return DictView(child_container, tx=transaction)

    def list_view(
        self, key: PathComponent, /, *, tx: Optional[ObservableKVTransaction] = None
    ) -> "ListView":
        """
        Get a list view for a child container.

        Creates the child container if it doesn't exist.

        Args:
            key: Key of child container
            tx: Optional transaction

        Returns:
            ListView: List view for child container

        Example:
            ```python
            # Access nested list
            skills = user.list_view("skills")
            skills.append("Python")
            ```
        """
        # Import here to avoid circular imports
        from .list_view import ListView

        transaction = tx or self._tx

        # Create child path
        child_path = self.container.path.join(key)

        # Check if child exists and is a container
        child = None
        if self.container.has_child(key, tx=transaction):
            child = self.container.get_child(key, tx=transaction)

            # If child exists but is not a container, remove it
            if child is not None and child.node_type() != NodeType.CONTAINER:
                self.container.remove_child(key, tx=transaction)
                child = None

        # Create container if needed
        if child is None:
            # Create a container with LIST protocols
            child = ContainerNode(
                self.container.backend,
                child_path,
                CommonContainerProtocols.LIST,
                tx=transaction,
            )

            # Set as child
            self.container.set_child(key, child, tx=transaction)

        # Ensure child has required protocols
        child_container = cast(ContainerNode, child)
        current_protocols = child_container.protocols(tx=transaction)
        required_protocols = CommonContainerProtocols.LIST

        # Update protocols if needed
        if (current_protocols & required_protocols) != required_protocols:
            child_container.update_protocols(current_protocols | required_protocols, tx=transaction)

        # Return view for child container
        return ListView(child_container, tx=transaction)

    def set_view(
        self, key: PathComponent, /, *, tx: Optional[ObservableKVTransaction] = None
    ) -> "SetView":
        """
        Get a set view for a child container.

        Creates the child container if it doesn't exist.

        Args:
            key: Key of child container
            tx: Optional transaction

        Returns:
            SetView: Set view for child container

        Example:
            ```python
            # Access nested set
            tags = user.set_view("tags")
            tags.add("important")
            ```
        """
        # Import here to avoid circular imports
        from .set_view import SetView

        transaction = tx or self._tx

        # Create child path
        child_path = self.container.path.join(key)

        # Check if child exists and is a container
        child = None
        if self.container.has_child(key, tx=transaction):
            child = self.container.get_child(key, tx=transaction)

            # If child exists but is not a container, remove it
            if child is not None and child.node_type() != NodeType.CONTAINER:
                self.container.remove_child(key, tx=transaction)
                child = None

        # Create container if needed
        if child is None:
            # Create a container with SET protocols
            child = ContainerNode(
                self.container.backend,
                child_path,
                CommonContainerProtocols.SET,
                tx=transaction,
            )

            # Set as child
            self.container.set_child(key, child, tx=transaction)

        # Ensure child has required protocols
        child_container = cast(ContainerNode, child)
        current_protocols = child_container.protocols(tx=transaction)
        required_protocols = CommonContainerProtocols.SET

        # Update protocols if needed
        if (current_protocols & required_protocols) != required_protocols:
            child_container.update_protocols(current_protocols | required_protocols, tx=transaction)

        # Return view for child container
        return SetView(child_container, tx=transaction)

    def flat_view(
        self, key: PathComponent, /, *, tx: Optional[ObservableKVTransaction] = None
    ) -> "FlatView":
        """
        Get a flat view for a child container.

        Creates the child container if it doesn't exist.

        Args:
            key: Key of child container
            tx: Optional transaction

        Returns:
            FlatView: Flat view for child container

        Example:
            ```python
            # Access flat dictionary
            settings = user.flat_view("settings")
            settings.set("theme", "dark")
            ```
        """
        # Import here to avoid circular imports
        from .flat_view import FlatView

        transaction = tx or self._tx

        # Create child path
        child_path = self.container.path.join(key)

        # Check if child exists and is a container
        child = None
        if self.container.has_child(key, tx=transaction):
            child = self.container.get_child(key, tx=transaction)

            # If child exists but is not a container, remove it
            if child is not None and child.node_type() != NodeType.CONTAINER:
                self.container.remove_child(key, tx=transaction)
                child = None

        # Create container if needed
        if child is None:
            # Create a container with FLAT_DICT protocols
            child = ContainerNode(
                self.container.backend,
                child_path,
                CommonContainerProtocols.FLAT_DICT,
                tx=transaction,
            )

            # Set as child
            self.container.set_child(key, child, tx=transaction)

        # Ensure child has required protocols
        child_container = cast(ContainerNode, child)
        current_protocols = child_container.protocols(tx=transaction)
        required_protocols = CommonContainerProtocols.FLAT_DICT

        # Update protocols if needed
        if (current_protocols & required_protocols) != required_protocols:
            child_container.update_protocols(current_protocols | required_protocols, tx=transaction)

        # Return view for child container
        return FlatView(child_container, tx=transaction)

    def view(
        self,
        key: PathComponent,
        view_class: type[ViewT],
        /,
        *,
        tx: Optional[ObservableKVTransaction] = None,
    ) -> ViewT:
        """
        Get a custom view for a child container.

        Creates the child container if it doesn't exist.

        Args:
            key: Key of child container
            view_class: View class to use
            tx: Optional transaction

        Returns:
            ViewT: Custom view for child container

        Example:
            ```python
            # Access with custom view
            custom_view = user.view("data", CustomView)
            ```
        """
        # Get required protocols from view class
        required_protocols = getattr(
            view_class, "required_protocols", lambda: ContainerProtocol.CONTAINER
        )()

        transaction = tx or self._tx

        # Create child path
        child_path = self.container.path.join(key)

        # Check if child exists and is a container
        child = None
        if self.container.has_child(key, tx=transaction):
            child = self.container.get_child(key, tx=transaction)

            # If child exists but is not a container, remove it
            if child is not None and child.node_type() != NodeType.CONTAINER:
                self.container.remove_child(key, tx=transaction)
                child = None

        # Create container if needed
        if child is None:
            # Create a container with required protocols
            child = ContainerNode(
                self.container.backend,
                child_path,
                required_protocols,
                tx=transaction,
            )

            # Set as child
            self.container.set_child(key, child, tx=transaction)

        # Ensure child has required protocols
        child_container = cast(ContainerNode, child)
        current_protocols = child_container.protocols(tx=transaction)

        # Update protocols if needed
        if (current_protocols & required_protocols) != required_protocols:
            child_container.update_protocols(current_protocols | required_protocols, tx=transaction)

        # Return view for child container
        return view_class(child_container, tx=transaction)

    def to_dict(self) -> Dict[PathComponent, Any]:
        """
        Convert to a Python dictionary.

        Returns:
            Dict[PathComponent, Any]: Dictionary representation

        Example:
            ```python
            user_dict = user.to_dict()
            ```
        """
        result = {}
        for key, value in self.items():
            result[key] = value
        return result
