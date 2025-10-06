"""
DictView implementation for the tree storage.

This module defines the DictView class, which provides a dictionary-like
interface for containers implementing the MAPPING structure.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generator, cast

import attrs

from ..node import ChildType
from ..types import EMPTY, ContainerProtocol, ContainerStructure, Empty, PathComponent, TreeT, Value
from .base import BaseView

if TYPE_CHECKING:
    from .list import ListView

__all__ = [
    "DictView",
]


@attrs.define(frozen=True, kw_only=True)
class DictView(BaseView[TreeT]):
    """
    Dictionary view for containers implementing the MAPPING structure.

    DictView provides a dictionary-like interface for interacting with
    containers, allowing key-based access and modification of child nodes.
    It supports standard dictionary operations like get, set, keys, values,
    items, as well as nested container access through other views.

    Example:
        ```python
        # Create a dictionary view
        users = tree.at("users").dict_view()

        # Set and get values
        users.set("alice", {"email": "alice@example.com"})
        alice_data = users.get("alice")

        # Check for keys
        if users.has("bob"):
            print("Bob exists")

        # Iterate over items
        for username, user_data in users.items():
            print(f"{username}: {user_data}")

        # Convert to regular dict
        users_dict = users.to_dict()

        # Access nested containers
        alice_profile = users.dict_view("alice")
        alice_profile.set("location", "San Francisco")
        ```
    """

    structure: ContainerStructure = attrs.field(default=ContainerStructure(1), init=False)

    protocol: ContainerProtocol = attrs.field(default=ContainerProtocol.MUTABLE, init=False)

    def extract(self):
        """
        Extract the value at the current path.

        Returns:
            Any: The value at the current path, which can be a primitive,
            a dict, a list, or a set depending on the container type.

        Raises:
            KeyError: If the key does not exist in the container.
            ContainerProtocolError: If the container is not a mapping container.
        """

        return {k: v for k, v in self.items()}

    def store(self, value: dict[PathComponent, Value], /, *, replace: bool = False) -> None:
        """
        Store a value at the specified key.

        Args:
            value: Value to store, which can be a primitive, dict, list, or set.
            replace: If True, replaces existing value at the path. Otherwise appends to existing list. Default is False.

        Raises:
            ContainerProtocolError: If the container is not a mapping container.
        """
        if not hasattr(value, "items"):
            raise ValueError(
                f"Expected a dict-like value, got {type(value).__name__}. "
                "Use `set` for single values or `store` for dict-like structures."
            )

        # If replacing, clear existing items
        if replace:
            self.clear()

        for k, v in value.items():
            self.set(k, v)

    def get(self, key: PathComponent, default: Value | Empty = EMPTY) -> Value | Empty:
        """
        Get value at key.

        For primitive values, returns the actual value.
        For container values, returns the converted Python object (dict/list/set).

        Args:
            key: Key to retrieve
            default: Default value if key doesn't exist

        Returns:
            Any: Value at key, Python object for containers, or default

        Example:
            ```python
            # Get primitive value
            email = users.get("alice", {}).get("email")

            # Get nested dict (returns actual dict, not view)
            alice_data = users.get("alice", {})  # Returns dict

            # Get with default
            status = users.get("alice", {}).get("status", "active")
            ```
        """

        return self._get_child_value(key, default=default)

    def set(self, key: PathComponent, value: Value) -> None:
        """
        Set value at key.

        Creates appropriate node type based on the value.
        Primitive values are stored directly.
        Dict values create nested mapping containers.
        List values create nested sequence containers.
        Set values create nested set containers.

        Args:
            key: Key to set
            value: Value to store

        Example:
            ```python
            # Set primitive value
            users.set("alice_email", "alice@example.com")

            # Set nested structure
            users.set("alice", {"email": "alice@example.com", "age": 30})

            # Set list structure
            users.set("alice_tasks", ["task1", "task2"])

            # Set set structure
            users.set("alice_tags", {"important", "user"})
            ```
        """
        self._set_child_value(key, value)

    def has(self, key: PathComponent) -> bool:
        """
        Check if key exists in the container.

        Args:
            key: Key to check

        Returns:
            bool: True if key exists

        Example:
            ```python
            if users.has("alice"):
                print("Alice exists")
            ```
        """
        return self.container.has_child(key) != ChildType.NOT_FOUND

    def remove(self, key: PathComponent) -> bool:
        """
        Remove key from the container.

        Args:
            key: Key to remove

        Returns:
            bool: True if key was removed, False if it didn't exist

        Example:
            ```python
            users.remove("alice")
            ```
        """
        return self.container.remove_child(key)

    def clear(self) -> int:
        """
        Remove all items from the container.

        Returns:
            int: Number of items removed

        Example:
            ```python
            users.clear()
            ```
        """
        return self.container.clear_children()

    def keys(self) -> Generator[PathComponent, None, None]:
        """
        Get all keys in the container.

        Returns:
            List[PathComponent]: List of keys

        Example:
            ```python
            for key in users.keys():
                print(f"User: {key}")
            ```
        """
        yield from self.container.keys()

    def values(self) -> Generator[Value, None, None]:
        """
        Get all values in the container.

        Returns:
            List[Any]: List of values (primitives or view objects)

        Example:
            ```python
            for value in users.values():
                print(f"Value: {value}")
            ```
        """
        for key in self.keys():
            yield cast(Value, self.get(key))

    def items(self) -> Generator[tuple[PathComponent, Value]]:
        """
        Get all key-value pairs in the container.

        Returns:
            List[Tuple[PathComponent, Any]]: List of (key, value) tuples

        Example:
            ```python
            for key, value in users.items():
                print(f"{key}: {value}")
            ```
        """
        for key in self.keys():
            value = cast(Value, self.get(key))
            yield (key, value)

    def dict_view(self, key: PathComponent) -> DictView:
        """
        Get a dictionary view for a nested container.

        Args:
            key: Key of the nested container

        Returns:
            DictView: Dictionary view for the nested container

        Raises:
            KeyError: If key doesn't exist
            ContainerProtocolError: If child is not a mapping container

        Example:
            ```python
            alice_profile = users.dict_view("alice")
            alice_profile.set("location", "San Francisco")
            ```
        """
        return self._dict_view(key)

    def list_view(self, key: PathComponent) -> "ListView":
        """
        Get a list view for a nested container.

        Args:
            key: Key of the nested container

        Returns:
            ListView: List view for the nested container

        Raises:
            KeyError: If key doesn't exist
            ContainerProtocolError: If child is not a sequence container

        Example:
            ```python
            alice_tasks = users.list_view("alice_tasks")
            alice_tasks.append("new task")
            ```
        """
        return self._list_view(key)
