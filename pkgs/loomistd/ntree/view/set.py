"""
SetView implementation for the tree storage.

This module defines the SetView class, which provides a set-like
interface for containers implementing the SET structure.
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Any, Set

import attrs

from ..transaction import with_transaction
from ..types import ContainerProtocol, ContainerStructure, Value
from .base import BaseView

if TYPE_CHECKING:
    from .dict import DictView
    from .list import ListView

__all__ = [
    "SetView",
]


@attrs.define(frozen=True, kw_only=True)
class SetView(BaseView):
    """
    Set view for containers implementing the SET structure.

    SetView provides a set-like interface for interacting with
    containers, allowing value-based operations for unique collections.
    It supports standard set operations like add, remove, contains, as well
    as nested container access through other views.

    Note: Set items are stored using their hash as keys, with the actual
    values stored as primitives. Complex objects are serialized.

    Example:
        ```python
        # Create a set view
        tags = tree.at("tags").set_view()

        # Add values
        tags.add("important")
        tags.add("urgent")
        tags.add("important")  # Duplicate ignored

        # Check membership
        if tags.contains("important"):
            print("Tag exists")

        # Remove values
        tags.remove("urgent")

        # Convert to regular set
        tags_set = tags.to_set()

        # Get size
        count = tags.size()
        ```
    """

    structure: ContainerStructure = attrs.field(
        default=ContainerStructure.SET_CONTAINER, init=False
    )

    protocol: ContainerProtocol = attrs.field(default=ContainerProtocol.SET, init=False)

    def get(self, value: Value, default: Value = None) -> Value:
        """
        Get value from set if it exists (mainly for consistency with other views).

        For primitive values, returns the actual value if found.
        For container values, returns the converted Python object (dict/list/set).

        Args:
            value: Value to look for
            default: Default value if not found

        Returns:
            Any: The value if found, Python object for containers, or default

        Example:
            ```python
            # Check if primitive value exists and get it
            tag = tags.get("important", "not found")

            # Get nested container value
            nested_data = tags.get({"type": "work"}, {})  # Returns dict if found
            ```
        """
        with with_transaction(self.container) as container:
            key = self._value_to_key(value)

            if not container.has_child(key):
                return default

            if container.is_child_primitive(key):
                return container.get_primitive_value(key)
            elif container.is_child_container(key):
                # Convert container to appropriate Python object
                child_view = self._get_child_view(key)
                if hasattr(child_view, "to_dict"):
                    return child_view.to_dict()
                elif hasattr(child_view, "to_list"):
                    return child_view.to_list()
                elif hasattr(child_view, "to_set"):
                    return child_view.to_set()
                else:
                    return default
            else:
                return default

    def add(self, value: Value) -> None:
        """
        Add value to the set if not already present.

        For primitive values, stores directly using hash as key.
        For complex values, serializes them first.

        Args:
            value: Value to add

        Example:
            ```python
            tags.add("important")
            tags.add("urgent")
            tags.add({"category": "work", "priority": 1})  # Complex object
            ```
        """
        with with_transaction(self.container) as container:
            key = self._value_to_key(value)

            # Check if already exists
            if not container.has_child(key):
                if isinstance(value, (dict, list, set)):
                    # For complex types, we need to create appropriate containers
                    self._set_value_with_type_detection(container, key, value)
                else:
                    # Store primitive value directly
                    container.set_primitive_value(key, value)

                # Update size metadata
                current_size = self.size()
                container.set_metadata("__size__", current_size + 1)

    def remove(self, value: Value) -> None:
        """
        Remove value from the set.

        Args:
            value: Value to remove

        Raises:
            KeyError: If value not in set

        Example:
            ```python
            tags.remove("important")
            ```
        """
        with with_transaction(self.container) as container:
            key = self._value_to_key(value)

            if not container.has_child(key):
                raise KeyError(f"Value {value} not in set")

            container.delete_child(key)

            # Update size metadata
            current_size = self.size()
            container.set_metadata("__size__", current_size - 1)

    def discard(self, value: Value) -> None:
        """
        Remove value from the set if present (no error if not found).

        Args:
            value: Value to remove

        Example:
            ```python
            tags.discard("maybe_exists")  # Won't raise error if not found
            ```
        """
        try:
            self.remove(value)
        except KeyError:
            pass

    def contains(self, value: Value) -> bool:
        """
        Check if value exists in the set.

        Args:
            value: Value to check

        Returns:
            bool: True if value exists

        Example:
            ```python
            if tags.contains("important"):
                print("Tag exists")
            ```
        """
        with with_transaction(self.container) as container:
            key = self._value_to_key(value)
            return container.has_child(key)

    def clear(self) -> None:
        """
        Remove all values from the set.

        Example:
            ```python
            tags.clear()
            ```
        """
        with with_transaction(self.container) as container:
            container.clear()
            container.set_metadata("__size__", 0)

    def size(self) -> int:
        """
        Get the number of unique values in the set.

        Returns:
            int: Number of unique values

        Example:
            ```python
            count = tags.size()
            ```
        """
        with with_transaction(self.container) as container:
            if not container.exists():
                return 0
            return container.get_metadata("__size__", 0)

    def is_empty(self) -> bool:
        """
        Check if the set is empty.

        Returns:
            bool: True if set has no elements

        Example:
            ```python
            if tags.is_empty():
                print("No tags")
            ```
        """
        return self.size() == 0

    def to_set(self) -> Set[Any]:
        """
        Convert container to a regular Python set.

        Note: Complex nested containers are converted to their Python
        equivalents before being added to the set.

        Returns:
            Set[Any]: Python set representation

        Example:
            ```python
            tags_set = tags.to_set()
            print(tags_set)
            # {'important', 'urgent', {'category': 'work'}}
            ```
        """
        with with_transaction(self.container) as container:
            if not container.exists():
                return set()

            result = set()

            # Iterate through all keys to reconstruct values
            for key in container.keys():
                if container.is_child_primitive(key):
                    value = container.get_primitive_value(key)
                    result.add(value)
                elif container.is_child_container(key):
                    # Recursively convert nested containers
                    child_view = self._get_child_view(key)
                    if hasattr(child_view, "to_set"):
                        # Convert nested set to frozenset
                        set_data = child_view.to_set()
                        result.add(frozenset(set_data))

            return result

    def union(self, other: SetView) -> Set[Any]:
        """
        Return union of this set with another set.

        Args:
            other: Another SetView

        Returns:
            Set[Any]: Union of both sets

        Example:
            ```python
            all_tags = tags1.union(tags2)
            ```
        """
        return self.to_set().union(other.to_set())

    def intersection(self, other: SetView) -> Set[Any]:
        """
        Return intersection of this set with another set.

        Args:
            other: Another SetView

        Returns:
            Set[Any]: Intersection of both sets

        Example:
            ```python
            common_tags = tags1.intersection(tags2)
            ```
        """
        return self.to_set().intersection(other.to_set())

    def difference(self, other: SetView) -> Set[Any]:
        """
        Return difference of this set with another set.

        Args:
            other: Another SetView

        Returns:
            Set[Any]: Values in this set but not in other

        Example:
            ```python
            unique_tags = tags1.difference(tags2)
            ```
        """
        return self.to_set().difference(other.to_set())

    # Cross-cutting view methods
    def dict_view(self, value: Value) -> DictView:
        """
        Get a dictionary view for a nested container by value.

        Args:
            value: Value that corresponds to a nested dict container

        Returns:
            DictView: Dictionary view for the nested container

        Raises:
            KeyError: If value doesn't exist
            ContainerProtocolError: If value is not a mapping container

        Example:
            ```python
            # If set contains complex objects stored as dicts
            tags.add({"type": "priority", "level": "high"})
            priority_dict = tags.dict_view({"type": "priority", "level": "high"})
            priority_dict.set("updated", True)
            ```
        """
        key = self._value_to_key(value)

        with with_transaction(self.container) as container:
            if not container.has_child(key):
                raise KeyError(f"Value {value} not in set")

        from .dict import DictView

        return DictView(
            backend=self.backend,
            path=self.path.join(key),
            tx=self.tx,
        )

    def list_view(self, value: Value) -> ListView:
        """
        Get a list view for a nested container by value.

        Args:
            value: Value that corresponds to a nested list container

        Returns:
            ListView: List view for the nested container

        Example:
            ```python
            # If set contains lists
            tags.add(["priority", "urgent"])
            priority_list = tags.list_view(["priority", "urgent"])
            priority_list.append("critical")
            ```
        """
        key = self._value_to_key(value)

        with with_transaction(self.container) as container:
            if not container.has_child(key):
                raise KeyError(f"Value {value} not in set")

        from .list import ListView

        return ListView(
            backend=self.backend,
            path=self.path.join(key),
            tx=self.tx,
        )

    def set_view(self, value: Value) -> SetView:
        """
        Get a set view for a nested container by value.

        Args:
            value: Value that corresponds to a nested set container

        Returns:
            SetView: Set view for the nested container

        Example:
            ```python
            # If set contains nested sets
            tags.add({"urgent", "important"})
            nested_set = tags.set_view({"urgent", "important"})
            nested_set.add("critical")
            ```
        """
        key = self._value_to_key(value)

        with with_transaction(self.container) as container:
            if not container.has_child(key):
                raise KeyError(f"Value {value} not in set")

        return SetView(
            backend=self.backend,
            path=self.path.join(key),
            tx=self.tx,
        )

    # Helper methods
    def _value_to_key(self, value: Value) -> str:
        """
        Convert a value to a deterministic string key for storage.

        Uses SHA-256 for consistent hashing across Python executions.
        This ensures data stored in one session can be retrieved in another.
        """
        if value is None:
            data_str = "None"
        elif isinstance(value, bool):
            # Handle bool before int since bool is a subclass of int
            data_str = f"bool:{value}"
        elif isinstance(value, (int, float)):
            data_str = f"{type(value).__name__}:{value}"
        elif isinstance(value, str):
            data_str = f"str:{value}"
        elif isinstance(value, dict):
            # Sort items for deterministic ordering
            sorted_items = sorted(value.items(), key=lambda x: str(x[0]))
            data_str = f"dict:{sorted_items}"
        elif isinstance(value, (list, tuple)):
            data_str = f"{type(value).__name__}:{list(value)}"
        elif isinstance(value, set):
            # Sort set items for deterministic ordering
            sorted_items = sorted(value, key=str)
            data_str = f"set:{sorted_items}"
        else:
            # Fallback for other types
            data_str = f"{type(value).__name__}:{str(value)}"

        # Create SHA-256 hash for consistent results
        hash_object = hashlib.sha256(data_str.encode("utf-8"))
        hash_hex = hash_object.hexdigest()

        # Use first 16 characters to keep keys reasonably short
        return f"_{hash_hex[:16]}"

    def _set_value_with_type_detection(self, container, key: str, value: Value) -> None:
        """Set value with automatic type detection and container creation."""
        if isinstance(value, dict):
            # Create nested mapping container
            from .dict import DictView

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

            try:
                # Try to determine structure from stored metadata
                from ..path import StructPath

                struct_path = StructPath(*child_path.components[1:])
                type_info = container.tx.get(struct_path.to_tuple())

                if isinstance(type_info, (list, tuple)) and len(type_info) == 2:
                    stored_structure = ContainerStructure(type_info[0])

                    if stored_structure & ContainerStructure.MAPPING_CONTAINER:
                        from .dict import DictView

                        return DictView(backend=self.backend, path=child_path, tx=self.tx)
                    elif stored_structure & ContainerStructure.SEQUENCE_CONTAINER:
                        from .list import ListView

                        return ListView(backend=self.backend, path=child_path, tx=self.tx)
                    elif stored_structure & ContainerStructure.SET_CONTAINER:
                        return SetView(backend=self.backend, path=child_path, tx=self.tx)

            except Exception:
                pass

            # Fallback to dict view
            from .dict import DictView

            return DictView(backend=self.backend, path=child_path, tx=self.tx)
