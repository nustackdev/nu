"""
DictView implementation for the tree storage.

This module defines the DictView class, which provides a dictionary-like
interface for containers implementing the MAPPING structure.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Tuple

import attrs

from ..exceptions import ContainerProtocolError
from ..types import ContainerProtocol, ContainerStructure, PathComponent, Value
from .base import BaseView

if TYPE_CHECKING:
    pass

__all__ = [
    "DictView",
]


@attrs.define(frozen=True, kw_only=True)
class DictView(BaseView):
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

    structure: ContainerStructure = attrs.field(
        default=ContainerStructure.MAPPING_CONTAINER, init=False
    )

    protocol: ContainerProtocol = attrs.field(default=ContainerProtocol.DICT, init=False)

    def get(self, key: PathComponent, default: Value = None) -> Value:
        """
        Get value at key.

        For primitive values, returns the actual value.
        For container values, returns a new DictView object for navigation.

        Args:
            key: Key to retrieve
            default: Default value if key doesn't exist

        Returns:
            Any: Value at key, DictView object for containers, or default

        Example:
            ```python
            # Get primitive value
            email = users.get("alice").get("email")

            # Get with default
            status = users.get("alice").get("status", "active")
            ```
        """
        container = self.container

        if not container.has_child(key):
            return default

        result = {}
        container = self.container

        if not container.exists():
            return result

        for key in self.keys():
            if container.is_child_primitive(key):
                result[key] = container.get_primitive_value(key)
            elif container.is_child_container(key):
                # Recursively convert nested containers
                try:
                    child_view = self.dict_view(key)
                    result[key] = child_view.to_dict()
                except (KeyError, ContainerProtocolError):
                    # If we can't create a dict view, skip this key
                    # This handles cases where the child container has incompatible structure
                    continue

        return result

    def set(self, key: PathComponent, value: Value) -> None:
        """
        Set value at key.

        Creates appropriate node type based on the value.
        Primitive values are stored directly.
        Dict values create nested mapping containers.
        List values would need ListView (not implemented here).

        Args:
            key: Key to set
            value: Value to store

        Example:
            ```python
            # Set primitive value
            users.set("alice_email", "alice@example.com")

            # Set nested structure
            users.set("alice", {"email": "alice@example.com", "age": 30})
            ```
        """
        container = self.container

        if isinstance(value, dict):
            # Create nested container and recursively set contents
            child_view = DictView(
                backend=self.backend,
                path=self.path.join(key),
                tx=self.tx,
            )
            for k, v in value.items():
                child_view.set(k, v)
        else:
            # Store primitive value directly
            container.set_primitive_value(key, value)

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
        return self.container.has_child(key)

    def delete(self, key: PathComponent) -> None:
        """
        Delete key from the container.

        Args:
            key: Key to delete

        Raises:
            KeyError: If key doesn't exist

        Example:
            ```python
            users.delete("alice")
            ```
        """
        self.container.delete_child(key)

    def clear(self) -> None:
        """
        Remove all items from the container.

        Example:
            ```python
            users.clear()
            ```
        """
        self.container.clear()

    def keys(self) -> List[PathComponent]:
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
        container = self.container
        if not container.exists():
            return []

        return list(container.keys())

    def values(self) -> List[Value]:
        """
        Get all values in the container.

        Returns:
            List[Any]: List of values (primitives or DictView objects)

        Example:
            ```python
            for value in users.values():
                print(f"Value: {value}")
            ```
        """
        return [self.get(key) for key in self.keys()]

    def items(self) -> List[Tuple[PathComponent, Value]]:
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
        return [(key, self.get(key)) for key in self.keys()]

    def update(self, other: Dict[PathComponent, Value]) -> None:
        """
        Update container with key-value pairs from another dict.

        Args:
            other: Dictionary to update from

        Example:
            ```python
            users.update({
                "alice": {"email": "alice@example.com"},
                "bob": {"email": "bob@example.com"}
            })
            ```
        """
        for key, value in other.items():
            self.set(key, value)

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
        return DictView(
            backend=self.backend,
            path=self.path.join(key),
            tx=self.tx,
        )

    def to_dict(self) -> Dict[PathComponent, Any]:
        """
        Convert container to a regular Python dictionary.

        Recursively converts nested containers to their Python equivalents:
        - Mapping containers become dicts
        - Primitive values remain as-is

        Returns:
            Dict[PathComponent, Any]: Python dictionary representation

        Example:
            ```python
            users_dict = users.to_dict()
            print(users_dict)
            # {'alice': {'email': 'alice@example.com', 'profile': {...}}}
            ```
        """
        result = {}
        container = self.container

        if not container.exists():
            return result

        for key in self.keys():
            if container.is_child_primitive(key):
                result[key] = container.get_primitive_value(key)
            elif container.is_child_container(key):
                # Recursively convert nested containers
                try:
                    child_view = self.dict_view(key)
                    result[key] = child_view.to_dict()
                except (KeyError, ContainerProtocolError):
                    # If we can't create a dict view, skip this key
                    # This handles cases where the child container has incompatible structure
                    continue

        return result
