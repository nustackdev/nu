"""
SetView implementation for the state management system.

This module defines the SetView class, which provides a set-like
interface for containers implementing the SET protocol.
"""

from __future__ import annotations

from typing import Any, List, Optional, Set

from .._core.primitive import PrimitiveNode
from .._core.transaction import TransactionContext
from .._exceptions import ContainerProtocolError
from .._state.backend import ObservableKVTransaction
from .._types import ContainerProtocol
from .view import BaseView

__all__ = ["SetView"]


class SetView(BaseView):
    """
    Set view for containers implementing the SET protocol.

    SetView provides a set-like interface for interacting with
    containers, allowing operations on unique values. It supports
    standard set operations like add, remove, contains, as well
    as conversion to Python sets or lists.

    Example:
        ```python
        # Create a set view
        tags = state.at("tags").set_view()

        # Add unique values
        tags.add("important")
        tags.add("featured")
        tags.add("important")  # Ignored (duplicate)

        # Check membership
        if tags.contains("important"):
            print("Tag exists")

        # Remove values
        tags.remove("featured")

        # Convert to Python set
        tag_set = tags.to_set()
        ```
    """

    @staticmethod
    def required_protocols() -> ContainerProtocol:
        """
        Get the protocols required by this view.

        Returns:
            ContainerProtocol: SET protocol
        """
        return ContainerProtocol.SET

    def _hash_value(self, value: Any, /) -> str:
        """
        Create a string hash key for a value.

        Args:
            value: Value to hash

        Returns:
            str: Hash key for the value
        """
        # Simple hash function - in real implementation, this would be more robust
        return f"value_{hash(str(value))}"

    def _store_with_hash(
        self, value: Any, /, *, tx: Optional[ObservableKVTransaction] = None
    ) -> None:
        """
        Store a value using its hash as the key.

        Args:
            value: Value to store
            tx: Optional transaction
        """
        with TransactionContext(self.container.backend, tx=self.tx) as transaction:
            # Get hash key for the value
            hash_key = self._hash_value(value)

            # Store the value
            self._store_value(hash_key, value)

            # Update the original value in a special metadata key to help with retrieval
            original_key = f"{hash_key}_original"
            child_path = self.container.path.join(original_key)
            primitive = PrimitiveNode(self.container.backend, child_path, tx=transaction)
            primitive.set_value(value, tx=transaction)

    def add(self, value: Any, /) -> None:
        """
        Add a value to the set.

        If the value already exists in the set, this operation has no effect.

        Args:
            value: Value to add

        Raises:
            ContainerProtocolError: If container doesn't support mutation

        Example:
            ```python
            tags.add("important")
            ```
        """
        with TransactionContext(self.container.backend, tx=self.tx) as transaction:
            # Validate container supports mutation
            if not self.container.supports_protocol(ContainerProtocol.MUTABLE):
                raise ContainerProtocolError(
                    f"Container at {self.container.path} does not support mutation"
                )

            # Skip if value already exists
            if self.contains(value):
                return

            # Store the value
            self._store_with_hash(value, tx=transaction)

    def remove(self, value: Any, /) -> None:
        """
        Remove a value from the set.

        If the value doesn't exist in the set, this operation has no effect.

        Args:
            value: Value to remove

        Raises:
            ContainerProtocolError: If container doesn't support mutation

        Example:
            ```python
            tags.remove("important")
            ```
        """
        with TransactionContext(self.container.backend, tx=self.tx) as transaction:
            # Validate container supports mutation
            if not self.container.supports_protocol(ContainerProtocol.MUTABLE):
                raise ContainerProtocolError(
                    f"Container at {self.container.path} does not support mutation"
                )

            # Skip if value doesn't exist
            if not self.contains(value):
                return

            # Get hash key for the value
            hash_key = self._hash_value(value)

            # Remove the value
            if self.container.has_child(hash_key, tx=transaction):
                self.container.remove_child(hash_key, tx=transaction)

            # Remove the original value metadata
            original_key = f"{hash_key}_original"
            if self.container.has_child(original_key, tx=transaction):
                self.container.remove_child(original_key, tx=transaction)

    def contains(self, value: Any, /) -> bool:
        """
        Check if a value exists in the set.

        Args:
            value: Value to check

        Returns:
            bool: True if the value exists in the set

        Example:
            ```python
            if tags.contains("important"):
                print("Tag exists")
            ```
        """
        with TransactionContext(self.container.backend, tx=self.tx) as transaction:
            # Get hash key for the value
            hash_key = self._hash_value(value)

            # Check if the hash key exists
            contains = self.container.has_child(hash_key, tx=transaction)
        return contains

    def clear(self) -> None:
        """
        Remove all values from the set.

        Raises:
            ContainerProtocolError: If container doesn't support mutation

        Example:
            ```python
            tags.clear()
            ```
        """
        with TransactionContext(self.container.backend, tx=self.tx) as transaction:
            # Validate container supports mutation
            if not self.container.supports_protocol(ContainerProtocol.MUTABLE):
                raise ContainerProtocolError(
                    f"Container at {self.container.path} does not support mutation"
                )

            # Clear the container
            self.container.clear(tx=transaction)

    def size(self) -> int:
        """
        Get the number of values in the set.

        Returns:
            int: Number of values in the set

        Example:
            ```python
            count = tags.size()
            ```
        """
        count = 0

        # Count non-special keys (those without the marker)
        keys = self.container.keys(tx=self._tx)
        for key in keys:
            # Skip special keys with markers and metadata keys
            if isinstance(key, str) and (
                self.container._MARKER in key or key.endswith("_original")
            ):
                continue
            count += 1

        return count

    def values(self) -> List[Any]:
        """
        Get all values in the set.

        Returns:
            List[Any]: List of values in the set

        Example:
            ```python
            all_tags = tags.values()
            ```
        """
        result = []

        # Get all keys
        keys = self.container.keys(tx=self._tx)

        for key in keys:
            # Skip special keys with markers and metadata keys
            if isinstance(key, str) and (
                self.container._MARKER in key or key.endswith("_original")
            ):
                continue

            # Get value from original metadata if possible
            original_key = f"{key}_original"
            if self.container.has_child(original_key, tx=self._tx):
                child = self.container.get_child(original_key, tx=self._tx)
                if child is not None:
                    value = self._extract_value(child)
                    if value is not None:
                        result.append(value)
            else:
                # Fall back to stored value
                child = self.container.get_child(key, tx=self._tx)
                if child is not None:
                    value = self._extract_value(child)
                    if value is not None:
                        result.append(value)

        return result

    def to_set(self) -> Set[Any]:
        """
        Convert to a Python set.

        Returns:
            Set[Any]: Set representation

        Example:
            ```python
            tag_set = tags.to_set()
            ```
        """
        return set(self.values())

    def to_list(self) -> List[Any]:
        """
        Convert to a Python list.

        Returns:
            List[Any]: List representation

        Example:
            ```python
            tag_list = tags.to_list()
            ```
        """
        return self.values()
