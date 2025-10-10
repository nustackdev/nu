# tree/view/protocols.py
"""Protocols for view data access.

This module defines the core protocol for container data access that all views must implement.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


__all__ = [
    "AccessibleViewProtocol",
]


@runtime_checkable
class AccessibleViewProtocol(Protocol):
    """Protocol defining the interface for container data access.

    All views must implement this protocol to provide consistent data access patterns.
    The protocol defines two levels of access:
    1. Key-based access: get/set individual items by key
    2. Bulk access: extract/store entire container contents
    """

    def get(self, key: Any, *args, **kwargs) -> Any:
        """Get value by key.

        Args:
            key: Key to retrieve (can be any type - str, int, custom objects)

        Returns:
            Value at the key location

        Raises:
            KeyError: If key doesn't exist
            TypeError: If key type not supported by this view

        Example:
            ```python
            # String key access
            user_name = view.get("name")

            # Integer key access
            first_item = view.get(0)

            # Custom key access
            node = view.get(NodeID("user_123"))
            ```
        """
        ...

    def set(self, key: Any, value: Any, *args, **kwargs) -> None:
        """Set value by key.

        Args:
            key: Key to set (can be any type - str, int, custom objects)
            value: Value to store

        Raises:
            KeyError: If key location cannot be created
            TypeError: If key type not supported by this view
            ValueError: If value type incompatible with container

        Example:
            ```python
            # String key assignment
            view.set("name", "Alice")

            # Integer key assignment
            view.set(0, "first_item")

            # Custom key assignment
            view.set(NodeID("user_123"), user_data)
            ```
        """
        ...

    def extract(self) -> Any:
        """Extract entire container contents as a single value.

        Returns the complete data structure that this view manages,
        typically as a Python native type (dict, list, etc.) or
        custom domain object.

        Returns:
            Complete container contents

        Example:
            ```python
            # Extract dict view as dictionary
            user_data = dict_view.extract()  # Returns: {"name": "Alice", "age": 30}

            # Extract list view as list
            items = list_view.extract()  # Returns: ["item1", "item2", "item3"]

            # Extract custom view as domain object
            document = document_view.extract()  # Returns: Document(title="...", content="...")
            ```
        """
        ...

    def store(self, value: Any, /, *, replace: bool = False) -> None:
        """Store entire container contents from a single value.

        Accepts a complete data structure and stores it in the container.
        The view determines how to interpret and store the value.

        Args:
            value: Complete data structure to store
            replace: If True, replaces existing contents. If False, merges with existing contents.

        Raises:
            TypeError: If value type incompatible with this view
            ValueError: If value structure invalid for this view

        Example:
            ```python
            # Store dictionary in dict view
            dict_view.store({"name": "Bob", "age": 25})

            # Store list in list view
            list_view.store(["new_item1", "new_item2"])

            # Store custom object in domain view
            document_view.store(Document(title="New Doc", content="..."))

            # Replace existing contents
            view.store(new_data, replace=True)

            # Merge with existing contents (if view supports it)
            view.store(additional_data, replace=False)
            ```
        """
        ...
