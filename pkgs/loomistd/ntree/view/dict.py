"""
DictView implementation for the tree storage.

This module defines the DictView class, which provides a dictionary-like
interface for containers implementing the MAPPING structure.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Tuple

import attrs

from ..exceptions import ContainerProtocolError
from ..transaction import with_transaction
from ..types import ContainerProtocol, ContainerStructure, PathComponent, Value
from .base import BaseView

if TYPE_CHECKING:
    from .list import ListView
    from .set import SetView

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

        with with_transaction(self.container) as container:
            result = {}

            if not container.exists():
                return result

            for key in self.keys():
                if container.is_child_primitive(key):
                    result[key] = container.get_primitive_value(key)
                elif container.is_child_container(key):
                    # Recursively convert nested containers
                    try:
                        child_view = self._get_child_view(key)
                        if hasattr(child_view, "to_dict"):
                            result[key] = child_view.to_dict()
                        elif hasattr(child_view, "to_list"):
                            result[key] = child_view.to_list()
                        elif hasattr(child_view, "to_set"):
                            result[key] = child_view.to_set()
                        else:
                            result[key] = None  # Fallback
                    except (KeyError, ContainerProtocolError):
                        # If we can't create a view, skip this key
                        continue

            return result

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
        with with_transaction(self.container) as container:
            self._set_value_with_type_detection(container, key, value)

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
        with with_transaction(self.container) as container:
            return container.has_child(key)

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
        with with_transaction(self.container) as container:
            container.delete_child(key)

    def clear(self) -> None:
        """
        Remove all items from the container.

        Example:
            ```python
            users.clear()
            ```
        """
        with with_transaction(self.container) as container:
            container.clear()

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
        with with_transaction(self.container) as container:
            if not container.exists():
                return []

            return list(container.keys())

    def values(self) -> List[Value]:
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

    def list_view(self, key: PathComponent) -> ListView:
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
        from .list import ListView

        return ListView(
            backend=self.backend,
            path=self.path.join(key),
            tx=self.tx,
        )

    def set_view(self, key: PathComponent) -> SetView:
        """
        Get a set view for a nested container.

        Args:
            key: Key of the nested container

        Returns:
            SetView: Set view for the nested container

        Raises:
            KeyError: If key doesn't exist
            ContainerProtocolError: If child is not a set container

        Example:
            ```python
            alice_tags = users.set_view("alice_tags")
            alice_tags.add("important")
            ```
        """
        from .set import SetView

        return SetView(
            backend=self.backend,
            path=self.path.join(key),
            tx=self.tx,
        )

    def to_dict(self) -> Dict[PathComponent, Any]:
        """
        Convert container to a regular Python dictionary.

        Recursively converts nested containers to their Python equivalents:
        - Mapping containers become dicts
        - Sequence containers become lists
        - Set containers become sets
        - Primitive values remain as-is

        Returns:
            Dict[PathComponent, Any]: Python dictionary representation

        Example:
            ```python
            users_dict = users.to_dict()
            print(users_dict)
            # {'alice': {'email': 'alice@example.com', 'tasks': [...], 'tags': {...}}}
            ```
        """
        with with_transaction(self.container) as container:
            result = {}

            if not container.exists():
                return result

            for key in self.keys():
                if container.is_child_primitive(key):
                    result[key] = container.get_primitive_value(key)
                elif container.is_child_container(key):
                    # Recursively convert nested containers
                    try:
                        child_view = self._get_child_view(key)
                        if hasattr(child_view, "to_dict"):
                            result[key] = child_view.to_dict()
                        elif hasattr(child_view, "to_list"):
                            result[key] = child_view.to_list()
                        elif hasattr(child_view, "to_set"):
                            result[key] = child_view.to_set()
                        else:
                            result[key] = None  # Fallback
                    except (KeyError, ContainerProtocolError):
                        # If we can't create a view, skip this key
                        continue

            return result

    # Helper methods
    def _set_value_with_type_detection(self, container, key: str, value: Value) -> None:
        """Set value with automatic type detection and container creation."""
        if isinstance(value, dict):
            # Create nested mapping container
            child_view = DictView(
                backend=self.backend,
                path=self.path.join(key),
                tx=container.tx,
            )
            for k, v in value.items():
                child_view.set(k, v)
        elif isinstance(value, list):
            # Create nested sequence container
            from .list import ListView

            child_view = ListView(
                backend=self.backend,
                path=self.path.join(key),
                tx=container.tx,
            )
            for item in value:
                child_view.append(item)
        elif isinstance(value, set):
            # Create nested set container
            from .set import SetView

            child_view = SetView(
                backend=self.backend,
                path=self.path.join(key),
                tx=container.tx,
            )
            for item in value:
                child_view.add(item)
        else:
            # Store primitive value directly
            container.set_primitive_value(key, value)

    def _get_child_view(self, key: str):
        """Get appropriate view for child container based on its structure."""
        with with_transaction(self.container) as container:
            # Get container structure from metadata
            child_path = self.path.join(key)
            child_container = container.__class__(
                backend=self.backend,
                path=child_path,
                structure=ContainerStructure.CONTAINER,  # Will be validated
                protocol=ContainerProtocol.DICT,  # Will be validated
                tx=container.tx,
            )

            try:
                # Try to determine structure from stored metadata
                from ..path import StructPath

                struct_path = StructPath(*child_path.components[1:])
                type_info = container.tx.get(struct_path.to_tuple())

                if isinstance(type_info, (list, tuple)) and len(type_info) == 2:
                    stored_structure = ContainerStructure(type_info[0])

                    if stored_structure & ContainerStructure.MAPPING_CONTAINER:
                        return DictView(backend=self.backend, path=child_path, tx=self.tx)
                    elif stored_structure & ContainerStructure.SEQUENCE_CONTAINER:
                        from .list import ListView

                        return ListView(backend=self.backend, path=child_path, tx=self.tx)
                    elif stored_structure & ContainerStructure.SET_CONTAINER:
                        from .set import SetView

                        return SetView(backend=self.backend, path=child_path, tx=self.tx)

            except Exception:
                pass

            # Fallback to dict view
            return DictView(backend=self.backend, path=child_path, tx=self.tx)
