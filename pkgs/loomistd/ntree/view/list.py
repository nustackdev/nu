"""
ListView implementation for the tree storage.

This module defines the ListView class, which provides a list-like
interface for containers implementing the SEQUENCE structure.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generator, cast

import attrs

from ..types import EMPTY, ContainerProtocol, ContainerStructure, Empty, Value
from .base import BaseView

if TYPE_CHECKING:
    from .dict import DictView

__all__ = [
    "ListView",
]


@attrs.define(frozen=True, kw_only=True)
class ListView(BaseView):
    """
    List view for containers implementing the SEQUENCE structure.

    ListView provides a list-like interface for interacting with
    containers, allowing index-based access and modification of elements.
    It supports standard list operations like append, insert, pop, as well
    as nested container access through other views.

    The ListView maintains a length metadata to track the current size
    of the list and uses integer indices for element access.

    Example:
        ```python
        # Create a list view
        tasks = tree.at("tasks").list_view()

        # Append values
        tasks.append("Complete project")
        tasks.append("Review code")

        # Get values by index
        first_task = tasks.get(0)

        # Insert at specific position
        tasks.insert(1, "Write tests")

        # Check length
        print(f"Tasks count: {len(tasks)}")

        # Iterate over items
        for i, task in enumerate(tasks):
            print(f"{i}: {task}")

        # Convert to regular list
        tasks_list = tasks.to_list()

        # Access nested containers
        task_details = tasks.dict_view(0)  # If first item is a dict
        task_details.set("priority", "high")
        ```
    """

    structure: ContainerStructure = attrs.field(
        default=ContainerStructure.SEQUENCE_CONTAINER, init=False
    )

    protocol: ContainerProtocol = attrs.field(default=ContainerProtocol.MUTABLE, init=False)

    # ========================================================================
    # Validation and Normalization Methods
    # ========================================================================

    def _normalize_index(self, index: int, *, allow_append: bool = False) -> int:
        """
        Normalize negative indices to positive ones.

        Args:
            index: Index to normalize (can be negative)
            allow_append: If True, allows index == length (for insert operations)

        Returns:
            int: Normalized positive index
        """
        length = self.length()

        if index < 0:
            index = length + index
            if allow_append and index < 0:
                index = 0
        elif allow_append:
            index = min(index, length)

        return index

    def _validate_index_bounds(self, index: int, *, allow_append: bool = False) -> None:
        """
        Validate that index is within bounds.

        Args:
            index: Normalized index to validate
            allow_append: If True, allows index == length

        Raises:
            IndexError: If index is out of bounds
        """
        length = self.length()
        max_index = length if allow_append else length - 1

        if length == 0 and not allow_append:
            raise IndexError("list index out of range (empty list)")
        if index < 0 or index > max_index:
            raise IndexError(f"list index {index} out of range (length: {length})")

    def _normalize_and_validate_index(self, index: int, *, allow_append: bool = False) -> int:
        """
        Normalize and validate index in one step.

        Args:
            index: Index to process
            allow_append: If True, allows index == length

        Returns:
            int: Normalized and validated index

        Raises:
            IndexError: If index is out of bounds
        """
        normalized = self._normalize_index(index, allow_append=allow_append)
        self._validate_index_bounds(normalized, allow_append=allow_append)
        return normalized

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _store_value_at_key(self, key: str, value: Value) -> None:
        """
        Store a value at the given key, handling both primitives and containers.

        Args:
            key: String key to store at
            value: Value to store
        """
        if self.is_value_primitive(value):
            self.container.set_primitive_value(key, value)
        else:
            child_view = self.get_view_for_value(key, value)
            child_view.store(value)

    def _move_element(self, from_index: int, to_index: int) -> None:
        """
        Move an element from one index to another.

        Args:
            from_index: Source index
            to_index: Destination index
        """
        from_key = str(from_index)
        to_key = str(to_index)

        if not self.container.has_child(from_key):
            return

        if self.container.is_child_primitive(from_key):
            # Move primitive value
            value = cast(Value, self.container.get_primitive_value(from_key))
            self.container.set_primitive_value(to_key, value)
        else:
            # Move container by extracting and re-storing
            child_info = self.container.get_child_info(from_key)
            if child_info.stored_structure and child_info.stored_protocol:
                old_view = self.get_view_for_container(
                    from_key, child_info.stored_structure, child_info.stored_protocol
                )
                value = cast(Value, old_view.extract())
                self._store_value_at_key(to_key, value)

        # Remove the old element
        self.container.remove_child(from_key)

    def _shift_elements_right(self, start_index: int, end_index: int) -> None:
        """
        Shift elements to the right by one position.

        Args:
            start_index: Starting index (inclusive)
            end_index: Ending index (exclusive)
        """
        for i in range(end_index - 1, start_index - 1, -1):
            self._move_element(i, i + 1)

    def _shift_elements_left(self, start_index: int, end_index: int) -> None:
        """
        Shift elements to the left by one position.

        Args:
            start_index: Starting index (inclusive)
            end_index: Ending index (exclusive)
        """
        for i in range(start_index, end_index):
            self._move_element(i, i - 1)

    # ========================================================================
    # CORE INTERFACE METHODS
    # ========================================================================

    def extract(self):
        """
        Extract the value at the current path.

        Returns:
            List: The list representation of the container contents.

        Raises:
            KeyError: If the container does not exist.
            ContainerProtocolError: If the container is not a sequence container.
        """
        return [v for v in self.values()]

    def store(self, value: list[Value], /) -> None:
        """
        Store a list value in the container.

        Args:
            value: List value to store, which can contain primitives, dicts, lists, or sets.

        Raises:
            ContainerProtocolError: If the container is not a sequence container.
            TypeError: If value is not a list or iterable.
        """
        if not hasattr(value, "__iter__") or isinstance(value, (str, bytes, dict)):
            raise TypeError(f"Expected iterable (excluding str/bytes/dict), got {type(value)}")

        # Clear existing content
        self.clear()

        # Add each item
        for item in value:
            self.append(item)

    def length(self) -> int:
        """
        Get the length of the list.

        Returns:
            int: Number of items in the list

        Example:
            ```python
            count = tasks.length()
            # or use len() builtin
            count = len(tasks)
            ```
        """
        return cast(int, self.container.get_metadata("__length__", 0))

    # ========================================================================
    # LIST ACCESS METHODS
    # ========================================================================

    def get(self, index: int, default: Value | Empty = EMPTY) -> Value | Empty:
        """
        Get value at index.

        For primitive values, returns the actual value.
        For container values, returns the converted Python object (dict/list/set).

        Args:
            index: Index to retrieve (supports negative indexing)
            default: Default value if index doesn't exist or is out of bounds

        Returns:
            Any: Value at index, Python object for containers, or default

        Example:
            ```python
            # Get by positive index
            first_item = tasks.get(0)

            # Get by negative index
            last_item = tasks.get(-1)

            # Get with default
            item = tasks.get(10, "not found")
            ```
        """
        # Handle empty list or out of bounds gracefully
        length = self.length()
        if length == 0:
            return default

        normalized_index = self._normalize_index(index)
        if normalized_index < 0 or normalized_index >= length:
            return default

        key = str(normalized_index)
        child_info = self.container.get_child_info(key)

        if self.container.is_child_primitive(key, child_info=child_info):
            return self.container.get_primitive_value(key, default=default, child_info=child_info)
        elif self.container.is_child_container(key, child_info=child_info):
            # Recursively convert nested containers
            child_structure = child_info.stored_structure
            child_protocol = child_info.stored_protocol

            if child_structure is None or child_protocol is None:
                return default

            view = self.get_view_for_container(key, child_structure, child_protocol)
            return view.extract()

        return default

    def set(self, index: int, value: Value) -> None:
        """
        Set value at index.

        Creates appropriate node type based on the value.
        Index must be within current bounds (0 <= index < length).

        Args:
            index: Index to set (supports negative indexing)
            value: Value to store

        Raises:
            IndexError: If index is out of bounds

        Example:
            ```python
            # Set by positive index
            tasks.set(0, "Updated first task")

            # Set by negative index
            tasks.set(-1, "Updated last task")

            # Set nested structure
            tasks.set(1, {"title": "Complex task", "priority": "high"})
            ```
        """
        normalized_index = self._normalize_and_validate_index(index)
        key = str(normalized_index)
        child_info = self.container.get_child_info(key)

        if self.container.has_child(key, child_info=child_info):
            # Child exists, check its type and handle accordingly
            if self.container.is_child_container(key, child_info=child_info):
                raise ValueError(
                    f"Index {index} already contains a container. Access it using the appropriate view to manipulate it."
                )
            elif self.container.is_child_primitive(key, child_info=child_info):
                # If the index contains a primitive, we can set it directly
                self.container.set_primitive_value(key, value)
                return

        # Store value based on its type
        self._store_value_at_key(key, value)

    # ========================================================================
    # LIST MUTATION METHODS
    # ========================================================================

    def append(self, value: Value) -> None:
        """
        Append value to the end of the list.

        Args:
            value: Value to append

        Example:
            ```python
            tasks.append("New task")
            tasks.append({"title": "Complex task", "done": False})
            ```
        """
        length = self.length()
        key = str(length)

        # Store value and update length
        self._store_value_at_key(key, value)
        self.container.set_metadata("__length__", length + 1)

    def insert(self, index: int, value: Value) -> None:
        """
        Insert value at the specified index.

        All elements at and after the index are shifted to the right.

        Args:
            index: Index to insert at (supports negative indexing)
            value: Value to insert

        Example:
            ```python
            # Insert at beginning
            tasks.insert(0, "Urgent task")

            # Insert at end (equivalent to append)
            tasks.insert(len(tasks), "Last task")

            # Insert in middle
            tasks.insert(2, "Middle task")
            ```
        """
        length = self.length()
        normalized_index = self._normalize_and_validate_index(index, allow_append=True)

        # Shift existing elements to the right
        self._shift_elements_right(normalized_index, length)

        # Insert the new value
        key = str(normalized_index)
        self._store_value_at_key(key, value)

        # Update length
        self.container.set_metadata("__length__", length + 1)

    def pop(self, index: int = -1) -> Value:
        """
        Remove and return item at index.

        Args:
            index: Index to remove (defaults to -1 for last item)

        Returns:
            Value: The removed value

        Raises:
            IndexError: If list is empty or index is out of bounds

        Example:
            ```python
            # Pop last item
            last_task = tasks.pop()

            # Pop first item
            first_task = tasks.pop(0)

            # Pop specific index
            middle_task = tasks.pop(2)
            ```
        """
        length = self.length()
        if length == 0:
            raise IndexError("pop from empty list")

        normalized_index = self._normalize_and_validate_index(index)

        # Get the value before removing
        value = self.get(normalized_index)
        if value is EMPTY:
            raise IndexError(f"No value at index {normalized_index}")

        # Remove the item
        key = str(normalized_index)
        self.container.remove_child(key)

        # Shift remaining elements to the left
        self._shift_elements_left(normalized_index + 1, length)

        # Update length
        self.container.set_metadata("__length__", length - 1)

        return cast(Value, value)

    def extend(self, iterable) -> None:
        """
        Extend list by appending elements from iterable.

        Args:
            iterable: Iterable of values to append

        Example:
            ```python
            tasks.extend(["Task 1", "Task 2", "Task 3"])
            ```
        """
        for item in iterable:
            self.append(item)

    def clear(self) -> None:
        """
        Remove all items from the list.

        Example:
            ```python
            tasks.clear()
            ```
        """
        self.container.clear()
        self.container.set_metadata("__length__", 0)

    # ========================================================================
    # ITERATION AND CONVERSION METHODS
    # ========================================================================

    def values(self) -> Generator[Value, None, None]:
        """
        Get all values in the list.

        Returns:
            Generator[Value]: Generator of values in order

        Example:
            ```python
            for value in tasks.values():
                print(f"Task: {value}")
            ```
        """
        for i in range(self.length()):
            yield cast(Value, self.get(i))

    # ========================================================================
    # NESTED VIEW ACCESS METHODS
    # ========================================================================

    def dict_view(self, index: int) -> DictView:
        """
        Get a dictionary view for a nested container at index.

        Args:
            index: Index of the nested container

        Returns:
            DictView: Dictionary view for the nested container

        Raises:
            IndexError: If index is out of bounds
            ContainerProtocolError: If item is not a mapping container

        Example:
            ```python
            task_details = tasks.dict_view(0)
            task_details.set("priority", "high")
            ```
        """
        normalized_index = self._normalize_and_validate_index(index)

        from .dict import DictView

        return DictView(
            backend=self.backend, path=self.path.join(str(normalized_index)), tx=self.tx
        )

    def list_view(self, index: int) -> ListView:
        """
        Get a list view for a nested container at index.

        Args:
            index: Index of the nested container

        Returns:
            ListView: List view for the nested container

        Raises:
            IndexError: If index is out of bounds
            ContainerProtocolError: If item is not a sequence container

        Example:
            ```python
            subtasks = tasks.list_view(0)
            subtasks.append("Subtask 1")
            ```
        """
        normalized_index = self._normalize_and_validate_index(index)

        return ListView(
            backend=self.backend, path=self.path.join(str(normalized_index)), tx=self.tx
        )
