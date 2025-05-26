"""
ListView implementation for the tree storage.

This module defines the ListView class, which provides a list-like
interface for containers implementing the SEQUENCE structure.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List

import attrs

from ..transaction import with_transaction
from ..types import ContainerProtocol, ContainerStructure, Value
from .base import BaseView

if TYPE_CHECKING:
    from .dict import DictView
    from .set import SetView

__all__ = [
    "ListView",
]


@attrs.define(frozen=True, kw_only=True)
class ListView(BaseView):
    """
    List view for containers implementing the SEQUENCE structure.

    ListView provides a list-like interface for interacting with
    containers, allowing index-based access and modification of child nodes.
    It supports standard list operations like get, set, append, insert, as well
    as nested container access through other views.

    Example:
        ```python
        # Create a list view
        tasks = tree.at("tasks").list_view()

        # Add values
        tasks.append("Setup project")
        tasks.append("Write documentation")

        # Get values by index
        first_task = tasks.get(0)

        # Set values by index
        tasks.set(1, "Update documentation")

        # Insert at specific position
        tasks.insert(1, "Create tests")

        # Convert to regular list
        tasks_list = tasks.to_list()

        # Access nested containers
        task_details = tasks.dict_view(0)  # First task as dict
        task_details.set("priority", "high")
        ```
    """

    structure: ContainerStructure = attrs.field(
        default=ContainerStructure.SEQUENCE_CONTAINER, init=False
    )

    protocol: ContainerProtocol = attrs.field(default=ContainerProtocol.LIST, init=False)

    def get(self, index: int, default: Value = None) -> Value:
        """
        Get value at index.

        For primitive values, returns the actual value.
        For container values, returns the converted Python object (dict/list/set).

        Args:
            index: Index to retrieve
            default: Default value if index doesn't exist

        Returns:
            Any: Value at index, Python object for containers, or default

        Example:
            ```python
            # Get primitive value
            first_task = tasks.get(0)

            # Get nested dict (returns actual dict, not view)
            task_data = tasks.get(1, {})  # Returns dict if container, default if not found

            # Get with default
            task = tasks.get(10, "No task")
            ```
        """
        with with_transaction(self.container) as container:
            if not container.exists():
                return default

            # Check if index is valid
            length = self.length()
            if index < 0:
                index = length + index  # Handle negative indexing

            if index < 0 or index >= length:
                return default

            key = str(index)

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

    def set(self, index: int, value: Value) -> None:
        """
        Set value at index.

        Creates appropriate node type based on the value.
        Primitive values are stored directly.
        Dict values create nested mapping containers.
        List values create nested sequence containers.
        Set values create nested set containers.

        Args:
            index: Index to set
            value: Value to store

        Raises:
            IndexError: If index is out of range

        Example:
            ```python
            # Set primitive value
            tasks.set(0, "Updated task")

            # Set nested structure
            tasks.set(1, {"name": "Complex task", "priority": "high"})
            ```
        """
        with with_transaction(self.container) as container:
            # Validate index
            length = self.length()
            if index < 0:
                index = length + index  # Handle negative indexing

            if index < 0 or index >= length:
                raise IndexError(f"Index {index} out of range for list of length {length}")

            key = str(index)
            self._set_value_with_type_detection(container, key, value)

    def append(self, value: Value) -> None:
        """
        Add value to the end of the list.

        Args:
            value: Value to append

        Example:
            ```python
            tasks.append("New task")
            tasks.append({"name": "Complex task", "due": "2024-01-01"})
            ```
        """
        with with_transaction(self.container) as container:
            length = self.length()
            key = str(length)
            self._set_value_with_type_detection(container, key, value)

            # Update length metadata
            container.set_metadata("__length__", length + 1)

    def insert(self, index: int, value: Value) -> None:
        """
        Insert value at specific index, shifting existing items.

        Args:
            index: Index to insert at
            value: Value to insert

        Example:
            ```python
            tasks.insert(1, "Priority task")
            ```
        """
        with with_transaction(self.container) as container:
            length = self.length()

            # Handle negative indexing and bounds
            if index < 0:
                index = max(0, length + index + 1)
            else:
                index = min(index, length)

            # Shift existing items
            for i in range(length - 1, index - 1, -1):
                old_key = str(i)
                new_key = str(i + 1)

                if container.is_child_primitive(old_key):
                    value_to_move = container.get_primitive_value(old_key)
                    container.set_primitive_value(new_key, value_to_move)
                    container.delete_child(old_key)
                elif container.is_child_container(old_key):
                    # Move container by recreating - this is expensive but correct
                    # In a real implementation, you'd want to optimize this
                    self._move_container(container, old_key, new_key)

            # Insert new value
            key = str(index)
            self._set_value_with_type_detection(container, key, value)

            # Update length metadata
            container.set_metadata("__length__", length + 1)

    def remove(self, index: int) -> None:
        """
        Remove value at index, shifting remaining items.

        Args:
            index: Index to remove

        Raises:
            IndexError: If index is out of range

        Example:
            ```python
            tasks.remove(0)  # Remove first task
            ```
        """
        with with_transaction(self.container) as container:
            length = self.length()
            if index < 0:
                index = length + index  # Handle negative indexing

            if index < 0 or index >= length:
                raise IndexError(f"Index {index} out of range for list of length {length}")

            # Remove the item
            key = str(index)
            container.delete_child(key)

            # Shift remaining items
            for i in range(index + 1, length):
                old_key = str(i)
                new_key = str(i - 1)

                if container.is_child_primitive(old_key):
                    value_to_move = container.get_primitive_value(old_key)
                    container.set_primitive_value(new_key, value_to_move)
                    container.delete_child(old_key)
                elif container.is_child_container(old_key):
                    self._move_container(container, old_key, new_key)

            # Update length metadata
            container.set_metadata("__length__", length - 1)

    def clear(self) -> None:
        """
        Remove all items from the list.

        Example:
            ```python
            tasks.clear()
            ```
        """
        with with_transaction(self.container) as container:
            container.clear()
            container.set_metadata("__length__", 0)

    def length(self) -> int:
        """
        Get the number of items in the list.

        Returns:
            int: Number of items

        Example:
            ```python
            count = tasks.length()
            ```
        """
        with with_transaction(self.container) as container:
            if not container.exists():
                return 0
            return container.get_metadata("__length__", 0)

    def to_list(self) -> List[Any]:
        """
        Convert container to a regular Python list.

        Recursively converts nested containers to their Python equivalents:
        - Mapping containers become dicts
        - Sequence containers become lists
        - Set containers become sets
        - Primitive values remain as-is

        Returns:
            List[Any]: Python list representation

        Example:
            ```python
            tasks_list = tasks.to_list()
            print(tasks_list)
            # ['Setup project', {'name': 'Complex task'}, ...]
            ```
        """
        with with_transaction(self.container) as container:
            if not container.exists():
                return []

            result = []
            length = self.length()

            for i in range(length):
                key = str(i)
                if container.is_child_primitive(key):
                    result.append(container.get_primitive_value(key))
                elif container.is_child_container(key):
                    # Recursively convert nested containers
                    child_view = self._get_child_view(key)
                    if hasattr(child_view, "to_dict"):
                        result.append(child_view.to_dict())
                    elif hasattr(child_view, "to_list"):
                        result.append(child_view.to_list())
                    elif hasattr(child_view, "to_set"):
                        result.append(child_view.to_set())
                    else:
                        result.append(None)  # Fallback

            return result

    # Cross-cutting view methods
    def dict_view(self, index: int) -> DictView:
        """
        Get a dictionary view for a nested container at index.

        Args:
            index: Index of the nested container

        Returns:
            DictView: Dictionary view for the nested container

        Raises:
            IndexError: If index is out of range
            ContainerProtocolError: If child is not a mapping container

        Example:
            ```python
            task_details = tasks.dict_view(0)
            task_details.set("priority", "high")
            ```
        """
        length = self.length()
        if index < 0:
            index = length + index

        if index < 0 or index >= length:
            raise IndexError(f"Index {index} out of range for list of length {length}")

        from .dict import DictView

        return DictView(
            backend=self.backend,
            path=self.path.join(str(index)),
            tx=self.tx,
        )

    def list_view(self, index: int) -> ListView:
        """
        Get a list view for a nested container at index.

        Args:
            index: Index of the nested container

        Returns:
            ListView: List view for the nested container

        Example:
            ```python
            subtasks = tasks.list_view(0)
            subtasks.append("Subtask 1")
            ```
        """
        length = self.length()
        if index < 0:
            index = length + index

        if index < 0 or index >= length:
            raise IndexError(f"Index {index} out of range for list of length {length}")

        return ListView(
            backend=self.backend,
            path=self.path.join(str(index)),
            tx=self.tx,
        )

    def set_view(self, index: int) -> SetView:
        """
        Get a set view for a nested container at index.

        Args:
            index: Index of the nested container

        Returns:
            SetView: Set view for the nested container

        Example:
            ```python
            tags = tasks.set_view(0)
            tags.add("important")
        """
        length = self.length()
        if index < 0:
            index = length + index

        if index < 0 or index >= length:
            raise IndexError(f"Index {index} out of range for list of length {length}")

        from .set import SetView

        return SetView(
            backend=self.backend,
            path=self.path.join(str(index)),
            tx=self.tx,
        )

    # Helper methods
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
                        from .dict import DictView

                        return DictView(backend=self.backend, path=child_path, tx=self.tx)
                    elif stored_structure & ContainerStructure.SEQUENCE_CONTAINER:
                        return ListView(backend=self.backend, path=child_path, tx=self.tx)
                    elif stored_structure & ContainerStructure.SET_CONTAINER:
                        from .set import SetView

                        return SetView(backend=self.backend, path=child_path, tx=self.tx)

            except Exception:
                pass

            # Fallback to dict view
            from .dict import DictView

            return DictView(backend=self.backend, path=child_path, tx=self.tx)

    def _move_container(self, container, old_key: str, new_key: str) -> None:
        """Move a container from old_key to new_key (expensive operation)."""
        # This is a simplified implementation - in practice you'd want to optimize this
        # by moving the container data at the storage level
        self.path.join(old_key)
        new_path = self.path.join(new_key)

        # Get the container view and convert to data
        child_view = self._get_child_view(old_key)
        if hasattr(child_view, "to_dict"):
            data = child_view.to_dict()
            # Recreate at new location
            from .dict import DictView

            new_view = DictView(backend=self.backend, path=new_path, tx=self.tx)
            new_view.update(data)
        elif hasattr(child_view, "to_list"):
            data = child_view.to_list()
            new_view = ListView(backend=self.backend, path=new_path, tx=self.tx)
            for item in data:
                new_view.append(item)
        elif hasattr(child_view, "to_set"):
            data = child_view.to_set()
            from .set import SetView

            new_view = SetView(backend=self.backend, path=new_path, tx=self.tx)
            for item in data:
                new_view.add(item)

        # Delete old container
        container.delete_child(old_key)
