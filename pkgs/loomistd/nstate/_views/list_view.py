"""
ListView implementation for the state management system.

This module defines the ListView class, which provides a list-like
interface for containers implementing the SEQUENCE protocol.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Optional

from .._core.primitive import PrimitiveNode
from .._core.transaction import TransactionContext
from .._exceptions import ContainerProtocolError, IndexOutOfBoundsError
from .._state.backend import ObservableKVTransaction
from .._types import CommonContainerProtocols, ContainerProtocol
from .._utils import is_empty
from .view import BaseView, ViewT

if TYPE_CHECKING:
    from .dict_view import DictView
    from .flat_view import FlatView
    from .set_view import SetView

__all__ = ["ListView"]


class ListView(BaseView):
    """
    List view for containers implementing the SEQUENCE protocol.

    ListView provides a list-like interface for interacting with
    containers, allowing index-based access and modification of child nodes.
    It supports standard list operations like append, insert, and remove,
    as well as nested container access through other views.

    Example:
        ```python
        # Create a list view
        tasks = state.at("tasks").list_view()

        # Add items
        tasks.append("Buy groceries")
        tasks.append("Clean house")

        # Get and set values
        first_task = tasks.get(0)
        tasks.set(1, "Clean entire house")

        # Insert and remove
        tasks.insert(1, "Do laundry")
        tasks.remove(0)

        # Convert to Python list
        task_list = tasks.to_list()
        ```
    """

    @staticmethod
    def required_protocols() -> ContainerProtocol:
        """
        Get the protocols required by this view.

        Returns:
            ContainerProtocol: SEQUENCE protocol
        """
        return ContainerProtocol.SEQUENCE

    def length(self) -> int:
        """
        Get the length of the list.

        Returns:
            int: Number of items in the list

        Example:
            ```python
            count = tasks.length()
            ```
        """
        with TransactionContext(self.container.backend, tx=self.tx) as transaction:
            # Get the list length from metadata
            length_key = self.container._LIST_LENGTH_KEY
            child_path = self.container.path.join(length_key)

            # Create primitive node for the length
            length_node = PrimitiveNode(self.container.backend, child_path, tx=transaction)
            length = length_node.get_value(tx=transaction)

            if length is None or is_empty(length):
                # No length stored yet, compute from keys
                keys = self.container.keys(tx=transaction)
                numeric_keys = []

                for key in keys:
                    try:
                        # Ignore special keys with markers
                        if isinstance(key, str) and self.container._MARKER in key:
                            continue
                        # Convert to integer
                        numeric_keys.append(int(key))
                    except (ValueError, TypeError):
                        # Skip non-numeric keys
                        pass

                # If no numeric keys, length is 0
                if not numeric_keys:
                    return 0

                # Length is max index + 1
                result = max(numeric_keys) + 1

                # Store computed length
                length_node.set_value(result, tx=transaction)
            else:
                # Use stored length
                result = int(length)

        return result

    def _update_length(
        self, new_length: int, /, *, tx: Optional[ObservableKVTransaction] = None
    ) -> None:
        """
        Update the stored list length.

        Args:
            new_length: New length to store
            tx: Optional transaction
        """
        with TransactionContext(self.container.backend, tx=self.tx) as transaction:
            # Update the list length metadata
            length_key = self.container._LIST_LENGTH_KEY
            child_path = self.container.path.join(length_key)

            # Create primitive node for the length
            length_node = PrimitiveNode(self.container.backend, child_path, tx=transaction)
            length_node.set_value(new_length, tx=transaction)

    def get(self, index: int, /) -> Any:
        """
        Get the value at an index.

        Args:
            index: Index to get value from

        Returns:
            Any: Value at the index, or None if index doesn't exist

        Raises:
            IndexOutOfBoundsError: If index is negative or >= length

        Example:
            ```python
            first_task = tasks.get(0)
            ```
        """
        length = self.length()

        # Handle negative indices
        if index < 0:
            index = length + index

        # Check bounds
        if index < 0 or index >= length:
            raise IndexOutOfBoundsError(f"Index {index} out of bounds for list of length {length}")

        # Convert index to string key
        key = str(index)

        # Check if child exists
        if not self.container.has_child(key, tx=self.tx):
            return None

        # Get child node
        child = self.container.get_child(key, tx=self.tx)
        if child is None:
            return None

        # Extract value from node
        return self._extract_value(child)

    def set(self, index: int, value: Any, /) -> None:
        """
        Set the value at an index.

        Args:
            index: Index to set value at
            value: Value to set

        Raises:
            IndexOutOfBoundsError: If index is negative or >= length
            ContainerProtocolError: If container doesn't support mutation

        Example:
            ```python
            tasks.set(0, "Updated task")
            ```
        """
        with TransactionContext(self.container.backend, tx=self.tx) as transaction:
            # Validate container supports mutation
            if not self.container.supports_protocol(ContainerProtocol.MUTABLE):
                raise ContainerProtocolError(
                    f"Container at {self.container.path} does not support mutation"
                )

            length = self.length()

            # Handle negative indices
            if index < 0:
                index = length + index

            # Check bounds
            if index < 0 or index >= length:
                raise IndexOutOfBoundsError(
                    f"Index {index} out of bounds for list of length {length}"
                )

            # Convert index to string key
            key = str(index)

            # Store value
            self._store_value(key, value)

    def append(self, value: Any, /) -> None:
        """
        Append a value to the end of the list.

        Args:
            value: Value to append

        Raises:
            ContainerProtocolError: If container doesn't support mutation

        Example:
            ```python
            tasks.append("New task")
            ```
        """
        with TransactionContext(self.container.backend, tx=self.tx) as transaction:
            # Validate container supports mutation
            if not self.container.supports_protocol(ContainerProtocol.MUTABLE):
                raise ContainerProtocolError(
                    f"Container at {self.container.path} does not support mutation"
                )

            # Get current length
            length = self.length()

            # Convert length to string key (appending at the end)
            key = str(length)

            # Store value
            self._store_value(key, value)

            # Update length
            self._update_length(length + 1, tx=transaction)

    def insert(self, index: int, value: Any, /) -> None:
        """
        Insert a value at an index, shifting items to the right.

        Args:
            index: Index to insert at
            value: Value to insert

        Raises:
            IndexOutOfBoundsError: If index is negative or > length
            ContainerProtocolError: If container doesn't support mutation

        Example:
            ```python
            tasks.insert(1, "New second task")
            ```
        """
        with TransactionContext(self.container.backend, tx=self.tx) as transaction:
            # Validate container supports mutation
            if not self.container.supports_protocol(ContainerProtocol.MUTABLE):
                raise ContainerProtocolError(
                    f"Container at {self.container.path} does not support mutation"
                )

            length = self.length()

            # Handle negative indices
            if index < 0:
                index = length + index

            # Check bounds (allow appending at the end)
            if index < 0 or index > length:
                raise IndexOutOfBoundsError(
                    f"Index {index} out of bounds for insert in list of length {length}"
                )

            # Shift elements to the right
            for i in range(length - 1, index - 1, -1):
                # Get item at i
                item = self.get(i)

                # Set at i+1
                key = str(i + 1)
                self._store_value(key, item)

            # Insert new value
            key = str(index)
            self._store_value(key, value)

            # Update length
            self._update_length(length + 1, tx=transaction)

    def remove(self, index: int, /) -> None:
        """
        Remove the value at an index, shifting items to the left.

        Args:
            index: Index to remove

        Raises:
            IndexOutOfBoundsError: If index is negative or >= length
            ContainerProtocolError: If container doesn't support mutation

        Example:
            ```python
            tasks.remove(0)  # Remove first task
            ```
        """
        with TransactionContext(self.container.backend, tx=self.tx) as transaction:
            # Validate container supports mutation
            if not self.container.supports_protocol(ContainerProtocol.MUTABLE):
                raise ContainerProtocolError(
                    f"Container at {self.container.path} does not support mutation"
                )

            length = self.length()

            # Handle negative indices
            if index < 0:
                index = length + index

            # Check bounds
            if index < 0 or index >= length:
                raise IndexOutOfBoundsError(
                    f"Index {index} out of bounds for list of length {length}"
                )

            # Shift elements to the left
            for i in range(index, length - 1):
                # Get item at i+1
                item = self.get(i + 1)

                # Set at i
                key = str(i)
                self._store_value(key, item)

            # Remove the last element
            last_key = str(length - 1)
            self.container.remove_child(last_key, tx=transaction)

            # Update length
            self._update_length(length - 1, tx=transaction)

    def clear(self) -> None:
        """
        Remove all items from the list.

        Raises:
            ContainerProtocolError: If container doesn't support mutation

        Example:
            ```python
            tasks.clear()
            ```
        """
        with TransactionContext(self.container.backend, tx=self.tx) as transaction:
            # Validate container supports mutation
            if not self.container.supports_protocol(ContainerProtocol.MUTABLE):
                raise ContainerProtocolError(
                    f"Container at {self.container.path} does not support mutation"
                )

            # Get all keys
            keys = self.container.keys(tx=transaction)

            # Remove all non-special keys
            for key in keys:
                if isinstance(key, str) and self.container._MARKER in key:
                    # Skip special keys (like length)
                    continue

                self.container.remove_child(key, tx=transaction)

            # Reset length to 0
            self._update_length(0, tx=transaction)

    def dict_view(
        self, index: int, /, *, tx: Optional[ObservableKVTransaction] = None
    ) -> "DictView":
        """
        Get a dictionary view for a child container at the given index.

        Creates the child container if it doesn't exist.

        Args:
            index: Index of child container
            tx: Optional transaction

        Returns:
            DictView: Dictionary view for child container

        Example:
            ```python
            # Get dictionary view for nested object
            user = users.get(0)
            profile = user.dict_view("profile")
            ```
        """
        # Import here to avoid circular imports
        from .dict_view import DictView

        transaction = tx or self.tx
        length = self.length()

        # Handle negative indices
        if index < 0:
            index = length + index

        # Check bounds
        if index < 0 or index >= length:
            raise IndexOutOfBoundsError(f"Index {index} out of bounds for list of length {length}")

        # Convert index to string key
        key = str(index)

        # Ensure child container exists with DICT protocol
        child_container = self._ensure_child_container(
            key, CommonContainerProtocols.DICT, tx=transaction
        )

        # Return dictionary view
        return DictView(child_container, tx=transaction)

    def list_view(
        self, index: int, /, *, tx: Optional[ObservableKVTransaction] = None
    ) -> "ListView":
        """
        Get a list view for a child container at the given index.

        Creates the child container if it doesn't exist.

        Args:
            index: Index of child container
            tx: Optional transaction

        Returns:
            ListView: List view for child container

        Example:
            ```python
            # Get list view for nested list
            user = users.get(0)
            tasks = user.list_view("tasks")
            ```
        """
        transaction = tx or self.tx
        length = self.length()

        # Handle negative indices
        if index < 0:
            index = length + index

        # Check bounds
        if index < 0 or index >= length:
            raise IndexOutOfBoundsError(f"Index {index} out of bounds for list of length {length}")

        # Convert index to string key
        key = str(index)

        # Ensure child container exists with LIST protocol
        child_container = self._ensure_child_container(
            key, CommonContainerProtocols.LIST, tx=transaction
        )

        # Return list view
        return ListView(child_container, tx=transaction)

    def set_view(self, index: int, /, *, tx: Optional[ObservableKVTransaction] = None) -> "SetView":
        """
        Get a set view for a child container at the given index.

        Creates the child container if it doesn't exist.

        Args:
            index: Index of child container
            tx: Optional transaction

        Returns:
            SetView: Set view for child container

        Example:
            ```python
            # Get set view for nested set
            user = users.get(0)
            tags = user.set_view("tags")
            ```
        """
        # Import here to avoid circular imports
        from .set_view import SetView

        transaction = tx or self.tx
        length = self.length()

        # Handle negative indices
        if index < 0:
            index = length + index

        # Check bounds
        if index < 0 or index >= length:
            raise IndexOutOfBoundsError(f"Index {index} out of bounds for list of length {length}")

        # Convert index to string key
        key = str(index)

        # Ensure child container exists with SET protocol
        child_container = self._ensure_child_container(
            key, CommonContainerProtocols.SET, tx=transaction
        )

        # Return set view
        return SetView(child_container, tx=transaction)

    def flat_view(
        self, index: int, /, *, tx: Optional[ObservableKVTransaction] = None
    ) -> "FlatView":
        """
        Get a flat view for a child container at the given index.

        Creates the child container if it doesn't exist.

        Args:
            index: Index of child container
            tx: Optional transaction

        Returns:
            FlatView: Flat view for child container

        Example:
            ```python
            # Get flat view for nested configuration
            user = users.get(0)
            settings = user.flat_view("settings")
            ```
        """
        # Import here to avoid circular imports
        from .flat_view import FlatView

        transaction = tx or self.tx
        length = self.length()

        # Handle negative indices
        if index < 0:
            index = length + index

        # Check bounds
        if index < 0 or index >= length:
            raise IndexOutOfBoundsError(f"Index {index} out of bounds for list of length {length}")

        # Convert index to string key
        key = str(index)

        # Ensure child container exists with FLAT_DICT protocol
        child_container = self._ensure_child_container(
            key, CommonContainerProtocols.FLAT_DICT, tx=transaction
        )

        # Return flat view
        return FlatView(child_container, tx=transaction)

    def view(
        self,
        index: int,
        view_class: type[ViewT],
        /,
        *,
        tx: Optional[ObservableKVTransaction] = None,
    ) -> ViewT:
        """
        Get a custom view for a child container at the given index.

        Creates the child container if it doesn't exist.

        Args:
            index: Index of child container
            view_class: View class to use
            tx: Optional transaction

        Returns:
            ViewT: Custom view for child container

        Example:
            ```python
            # Get custom view for nested container
            custom_view = list.view(0, CustomView)
            ```
        """
        # Get required protocols from view class
        required_protocols = getattr(
            view_class, "required_protocols", lambda: ContainerProtocol.CONTAINER
        )()

        transaction = tx or self.tx
        length = self.length()

        # Handle negative indices
        if index < 0:
            index = length + index

        # Check bounds
        if index < 0 or index >= length:
            raise IndexOutOfBoundsError(f"Index {index} out of bounds for list of length {length}")

        # Convert index to string key
        key = str(index)

        # Ensure child container exists with required protocols
        child_container = self._ensure_child_container(key, required_protocols, tx=transaction)

        # Return custom view
        return view_class(child_container, tx=transaction)

    def to_list(self) -> List[Any]:
        """
        Convert to a Python list.

        Returns:
            List[Any]: List representation

        Example:
            ```python
            task_list = tasks.to_list()
            ```
        """
        length = self.length()
        result = [None] * length

        for i in range(length):
            result[i] = self.get(i)

        return result
