"""
ListView implementation for the tree storage.

This module defines the ListView class, which provides a list-like
interface for containers implementing the SEQUENCE structure.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Generator, cast

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

    LENGTH_MARKER: ClassVar[str] = "L"

    def _validate_index_with_length(self, index: int) -> tuple[int, int]:
        """
        Validate and normalize index for regular list operations, returning both index and length.

        Optimized to read length only once from storage and return it for reuse.
        Follows Python semantics: valid range is 0 <= index < len(list)

        Args:
            index: Index to validate (can be negative)

        Returns:
            tuple[int, int]: (validated_index, length)

        Raises:
            IndexError: If index is out of bounds

        Examples:
            For list of length 3: [a, b, c]
            - _validate_index_with_length(0) → (0, 3)
            - _validate_index_with_length(-1) → (2, 3)
            - _validate_index_with_length(3) → IndexError
            - _validate_index_with_length(-4) → IndexError
        """
        length = self.length()

        # Handle empty list
        if length == 0:
            raise IndexError("list index out of range")

        # Normalize negative indices
        if index < 0:
            normalized_index = length + index
        else:
            normalized_index = index

        # Validate bounds (Python allows 0 to length-1)
        if normalized_index < 0 or normalized_index >= length:
            raise IndexError("list index out of range")

        return normalized_index, length

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
        return cast(int, self.container.get_metadata(self.LENGTH_MARKER, 0))

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
        index, length = self._validate_index_with_length(index)

        key = str(index)

        return self._get_child_value(key, default=default)

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

        self._set_child_value(key, value)
        self.container.set_metadata(self.LENGTH_MARKER, length + 1)

    def pop(self) -> Value:
        """
        Remove and return the last item.

        Returns:
            Value: The removed value

        Raises:
            IndexError: If list is empty

        Example:
            ```python
            # Pop last item
            last_task = tasks.pop()
            ```
        """
        length = self.length()
        if length == 0:
            raise IndexError("Pop from empty list")

        index = length - 1
        key = str(index)

        last_item = self.get(index)

        self.container.remove_child(key)

        # Update length
        self.container.set_metadata(self.LENGTH_MARKER, length - 1)

        return cast(Value, last_item)

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
        self.container.clear_children()
        self.container.delete_metadata(self.LENGTH_MARKER)

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
        normalized_index, _ = self._validate_index_with_length(index)

        return self._dict_view(str(normalized_index))

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

        normalized_index, _ = self._validate_index_with_length(index)

        return self._list_view(str(normalized_index))
