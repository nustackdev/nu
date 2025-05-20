"""
DictView implementation for the state management system.

This module defines the DictView class, which provides a dictionary-like
interface for containers implementing the MAPPING protocol.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from .._exceptions import ContainerProtocolError
from .._state.backend import ObservableKVTransaction
from .._types import CommonContainerProtocols, ContainerProtocol, PathComponent
from .._utils import TransactionContext
from .view import BaseView, ViewT

if TYPE_CHECKING:
    from .flat_view import FlatView
    from .list_view import ListView
    from .set_view import SetView

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

        # Extract value from node using helper method
        return self._extract_value(child)

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
        with TransactionContext(self.container.backend, self._tx) as transaction:
            # Validate container supports mutation
            if not self.container.supports_protocol(ContainerProtocol.MUTABLE):
                raise ContainerProtocolError(
                    f"Container at {self.container.path} does not support mutation"
                )

            # Store value using helper method
            self._store_value(key, value)

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

        # Ensure child container exists with DICT protocol using helper method
        child_container = self._ensure_child_container(
            key, CommonContainerProtocols.DICT, tx=transaction
        )

        # Return dictionary view
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

        # Ensure child container exists with LIST protocol using helper method
        child_container = self._ensure_child_container(
            key, CommonContainerProtocols.LIST, tx=transaction
        )

        # Return list view
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

        # Ensure child container exists with SET protocol using helper method
        child_container = self._ensure_child_container(
            key, CommonContainerProtocols.SET, tx=transaction
        )

        # Return set view
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

        # Ensure child container exists with FLAT_DICT protocol using helper method
        child_container = self._ensure_child_container(
            key, CommonContainerProtocols.FLAT_DICT, tx=transaction
        )

        # Return flat view
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

        # Ensure child container exists with required protocols using helper method
        child_container = self._ensure_child_container(key, required_protocols, tx=transaction)

        # Return custom view
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
