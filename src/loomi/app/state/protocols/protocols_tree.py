from __future__ import annotations

from typing import TYPE_CHECKING, Any, AsyncIterator, Callable, Iterator, Protocol, overload

from ..types import StatePath, StatePathComponent, StateValue

if TYPE_CHECKING:
    from .protocols_kv import AsyncTransactionProtocol, SyncTransactionProtocol

__all__ = [
    "AsyncStateNodeProtocol",
    "AsyncStateDictProtocol",
    "AsyncStateListProtocol",
    "SyncStateNodeProtocol",
    "SyncStateDictProtocol",
    "SyncStateListProtocol",
]

# --- Protocols for asynchronous state handling --- #


class AsyncStateNodeProtocol(Protocol):
    """
    Protocol for state tree nodes.

    This abstract base class provides common functionality for both dictionary
    and list state nodes, allowing them to share code for nested node access,
    transformations, filtering, and other common operations.

    AsyncStateNodeProtocol serves as a consistent interface for working with nodes,
    regardless of their type (dictionary or list).
    """

    @property
    def path(self) -> StatePath:
        """
        Get the base path for this state node.

        Returns:
            The base path
        """
        ...

    async def dict(
        self,
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "AsyncTransactionProtocol | None" = None,
    ) -> AsyncStateDictProtocol:
        """
        Get a nested dictionary node interface.

        Args:
            path: First path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            A new AsyncStateDictProtocol instance for the nested dictionary node
        """
        ...

    async def list(
        self,
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "AsyncTransactionProtocol | None" = None,
    ) -> AsyncStateListProtocol:
        """
        Get a nested list node interface.

        Args:
            path: First path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            A new AsyncStateListProtocol instance for the nested list node
        """
        ...

    @overload
    async def remove(
        self,
        txn: "AsyncTransactionProtocol | None" = None,
    ) -> None: ...

    @overload
    async def remove(
        self,
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "AsyncTransactionProtocol | None" = None,
    ) -> None: ...

    async def remove(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Delete a node from the state tree.

        When called with no path arguments, deletes the current node.
        When called with path segments, deletes the specified nested node.

        Args:
            path: Optional first path segment
            *paths: Additional path segments
            txn: Optional transaction to use
        """
        ...

    @overload
    async def exists(
        self,
        txn: "AsyncTransactionProtocol | None" = None,
    ) -> bool: ...

    @overload
    async def exists(
        self,
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "AsyncTransactionProtocol | None" = None,
    ) -> bool: ...

    async def exists(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Check if a node exists in the state tree.

        When called with no path arguments, checks if the current node exists.
        When called with path segments, checks if the specified nested node exists.

        Args:
            path: Optional first path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            True if the node exists, False otherwise
        """
        ...

    @overload
    async def is_dict(
        self,
        txn: "AsyncTransactionProtocol | None" = None,
    ) -> bool: ...

    @overload
    async def is_dict(
        self,
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "AsyncTransactionProtocol | None" = None,
    ) -> bool: ...

    async def is_dict(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Check if a node is a dictionary node.

        When called with no path arguments, checks if the current node is a dictionary.
        When called with path segments, checks if the specified nested node is a dictionary.

        Args:
            path: Optional first path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            True if the node is a dictionary, False otherwise
        """
        ...

    @overload
    async def is_list(
        self,
        txn: "AsyncTransactionProtocol | None" = None,
    ) -> bool: ...

    @overload
    async def is_list(
        self,
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "AsyncTransactionProtocol | None" = None,
    ) -> bool: ...

    async def is_list(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Check if a node is a list node.

        When called with no path arguments, checks if the current node is a list.
        When called with path segments, checks if the specified nested node is a list.

        Args:
            path: Optional first path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            True if the node is a list, False otherwise
        """
        ...

    @overload
    async def to_python_object(
        self,
        txn: "AsyncTransactionProtocol | None" = None,
    ) -> StateValue: ...

    @overload
    async def to_python_object(
        self,
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "AsyncTransactionProtocol | None" = None,
    ) -> StateValue: ...

    async def to_python_object(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> StateValue:
        """
        Convert a node to a standard Python object.

        When called with no path arguments, converts the current node.
        When called with path segments, converts the specified nested node.

        Args:
            path: Optional first path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            The Python representation of the node

        Raises:
            KeyError: If the node doesn't exist
        """
        ...

    async def copy_to(
        self,
        target: StatePathComponent,
        /,
        *targets: StatePathComponent,
        txn: "AsyncTransactionProtocol | None" = None,
    ) -> None:
        """
        Create a copy of this node at another location in the state tree.

        Args:
            target: First segment of the target path
            *targets: Additional segments of the target path
            txn: Optional transaction to use
        """
        ...

    async def move_to(
        self,
        target: StatePathComponent,
        /,
        *targets: StatePathComponent,
        txn: "AsyncTransactionProtocol | None" = None,
    ) -> None:
        """
        Move this node to another location in the state tree.

        This operation is atomic - either the move completes successfully,
        or no changes are made to the state tree.

        Args:
            target: First segment of the target path
            *targets: Additional segments of the target path
            txn: Optional transaction to use

        Note:
            After this operation, the current AsyncStateNodeProtocol instance should not be used
            as its path is no longer valid.
        """
        ...

    @overload
    async def transform(
        self,
        transform_func: Callable[[StateValue], StateValue],
        txn: "AsyncTransactionProtocol | None" = None,
    ) -> None: ...

    @overload
    async def transform(
        self,
        transform_func: Callable[[StateValue], StateValue],
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "AsyncTransactionProtocol | None" = None,
    ) -> None: ...

    async def transform(
        self,
        transform_func: Callable[[StateValue], StateValue],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Apply a transformation function to a node.

        The transformation function takes the current value as a Python object
        and returns a new transformed Python object.

        When called with just the transform function, transforms the current node.
        When called with path segments, transforms the specified nested node.

        Args:
            transform_func: Function that takes a Python object and returns a transformed version
            path: Optional first path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Raises:
            KeyError: If the node doesn't exist
            TypeError: If the transformation result is not of a compatible type
        """
        ...

    @overload
    async def filter(
        self,
        filter_func: Callable[[StateValue], bool] | Callable[[str, StateValue], bool],
        txn: "AsyncTransactionProtocol | None" = None,
    ) -> None: ...

    @overload
    async def filter(
        self,
        filter_func: Callable[[StateValue], bool] | Callable[[str, StateValue], bool],
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "AsyncTransactionProtocol | None" = None,
    ) -> None: ...

    async def filter(
        self,
        filter_func: Callable[[StateValue], bool] | Callable[[str, StateValue], bool],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Filter elements of a list or dictionary node.

        For list nodes, filter_func takes (value) and returns a boolean.
        For dictionary nodes, filter_func takes (key, value) and returns a boolean.

        Elements for which filter_func returns False will be removed.

        When called with just the filter function, filters the current node.
        When called with path segments, filters the specified nested node.

        Args:
            filter_func: Function that takes elements and returns whether to keep them
            path: Optional first path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Raises:
            TypeError: If the node is neither a list nor a dictionary
            KeyError: If the node doesn't exist
        """
        ...

    @overload
    async def map(
        self,
        map_func: Callable[[StateValue], StateValue],
        txn: "AsyncTransactionProtocol | None" = None,
    ) -> None: ...

    @overload
    async def map(
        self,
        map_func: Callable[[StateValue], StateValue],
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "AsyncTransactionProtocol | None" = None,
    ) -> None: ...

    async def map(
        self,
        map_func: Callable[[StateValue], StateValue],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Apply a mapping function to each element in a list or dictionary node.

        For list nodes, each element is replaced with the result of map_func(element).
        For dictionary nodes, each value is replaced with the result of map_func(value).

        This is a convenience method that transforms the node by applying the map function
        to each element while preserving the structure.

        When called with just the map function, maps the current node elements.
        When called with path segments, maps the specified nested node elements.

        Args:
            map_func: Function to apply to each element
            path: Optional first path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Raises:
            TypeError: If the node is neither a list nor a dictionary
            KeyError: If the node doesn't exist
            TypeError: If the mapping result contains unsupported types
        """
        ...

    @overload
    async def store(
        self,
        value: StateValue,
        txn: "AsyncTransactionProtocol | None" = None,
    ) -> None: ...

    @overload
    async def store(
        self,
        value: StateValue,
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "AsyncTransactionProtocol | None" = None,
    ) -> None: ...

    async def store(
        self,
        value: StateValue,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Store a Python object at a specified node.

        This is a convenience method for directly storing Python objects
        (dictionaries, lists, or primitive values) in the state tree.

        When called with just the value, replaces the current node.
        When called with path segments, stores at the specified nested node.

        Args:
            value: Python object to store
            path: Optional first path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Raises:
            TypeError: If the value is of an unsupported type
        """
        ...


class AsyncStateDictProtocol(AsyncStateNodeProtocol, Protocol):
    """
    Protocol for dictionary-like interface to state storage.

    This class provides an interface similar to a Python dictionary
    for interacting with dictionary nodes in the state storage.
    It implements async methods for dictionary operations that map
    to the underlying state structure.

    Usage:
        # Create or access a dictionary node
        state_dict = await async_state.dict("users", "123")

        # Set values
        await state_dict.set("name", "Alice")
        await state_dict.set("settings", {"theme": "dark", "notifications": True})

        # Get values
        name = await state_dict.get("name")
        theme = await state_dict.get("settings", "theme")

        # Delete values
        await state_dict.delete("settings")

        # Check if a key exists
        if await state_dict.contains("email"):
            email = await state_dict.get("email")
    """

    async def get(
        self, path: StatePathComponent, /, *paths: StatePathComponent, default: Any = None
    ) -> StateValue:
        """
        Get a value from the dictionary node.

        Args:
            path: First path segment
            *paths: Additional path segments
            default: Value to return if path doesn't exist

        Returns:
            The value associated with the path, or default if not found
        """
        ...

    async def set(
        self, path: StatePathComponent, /, *paths: StatePathComponent, value: StateValue
    ) -> None:
        """
        Set a value in the dictionary node.

        Args:
            path: First path segment
            *paths_and_value: Additional path segments followed by the value to set

        Raises:
            ValueError: If no value is provided
        """
        ...

    async def delete(self, path: StatePathComponent, /, *paths: StatePathComponent) -> None:
        """
        Delete a path from the dictionary node.

        Args:
            path: First path segment
            *paths: Additional path segments

        Raises:
            KeyError: If the path doesn't exist
        """
        ...

    async def contains(self, path: StatePathComponent, /, *paths: StatePathComponent) -> bool:
        """
        Check if a path exists in the dictionary node.

        Args:
            path: First path segment
            *paths: Additional path segments

        Returns:
            True if the path exists, False otherwise
        """
        ...

    async def keys(self) -> list[StatePathComponent]:
        """
        Get all top-level keys in the dictionary node.

        Returns:
            List of keys in the dictionary
        """
        ...

    async def values(self) -> list[StateValue]:
        """
        Get all top-level values in the dictionary node.

        Returns:
            List of values in the dictionary
        """
        ...

    async def items(self) -> list[tuple[StatePathComponent, StateValue]]:
        """
        Get all top-level key-value pairs in the dictionary node.

        Returns:
            List of (key, value) tuples
        """
        ...

    async def to_dict(self) -> dict[StatePathComponent, StateValue]:
        """
        Convert to a regular Python dictionary.

        Returns:
            Python dictionary containing all data from this dictionary node
        """
        ...

    async def update(self, other: dict[StatePathComponent, StateValue]) -> None:
        """
        Update the dictionary node with key-value pairs from another dictionary.

        Args:
            other: Dictionary containing key-value pairs to update
        """
        ...

    async def clear(self) -> None:
        """
        Remove all items from the dictionary node.
        """
        ...

    async def pop(self, key: StatePathComponent, default: StateValue = None) -> StateValue:
        """
        Remove and return a value from the dictionary node.

        Args:
            key: Key to remove
            default: Value to return if key doesn't exist

        Returns:
            The value associated with the key, or default if not found

        Raises:
            KeyError: If the key doesn't exist and no default is provided
        """
        ...

    async def setdefault(self, key: StatePathComponent, default: StateValue = None) -> StateValue:
        """
        Return the value for key if it exists, otherwise set it to default.

        Args:
            key: Key to check and potentially set
            default: Value to set and return if key doesn't exist

        Returns:
            The value associated with the key, or default if not found
        """
        ...

    async def __len__(self) -> int:
        """
        Get the number of items in the dictionary node.

        Returns:
            The number of items
        """
        ...

    async def __aiter__(self) -> AsyncIterator[StatePathComponent]:
        """
        Get an async iterator over the keys.

        Returns:
            Async iterator yielding keys
        """
        ...


class AsyncStateListProtocol(AsyncStateNodeProtocol):
    """
    Protocol for list-like interface to state storage.

    This class provides an interface similar to a Python list
    for interacting with list nodes in the state storage.
    It implements async methods for list operations that map
    to the underlying state structure.

    Usage:
        # Create or access a list node
        state_list = await async_state.list("users", "123", "posts")

        # Append items
        await state_list.append("New post content")

        # Get items
        first_post = await state_list.get(0)

        # Set items
        await state_list.set(1, "Updated post content")

        # Remove items
        await state_list.delete(2)

        # Get the length
        length = await state_list.length()
    """

    async def get(self, index: int) -> StateValue:
        """
        Get an item from the list node at the specified index.

        Args:
            index: Index of the item to retrieve

        Returns:
            The item at the specified index

        Raises:
            IndexError: If the index is out of range
        """
        ...

    async def set(self, index: int, value: StateValue) -> None:
        """
        Set an item in the list node at the specified index.

        Args:
            index: Index of the item to set
            value: Value to set

        Raises:
            IndexError: If the index is out of range
        """
        ...

    async def append(self, value: StateValue) -> int:
        """
        Append an item to the list node.

        Args:
            value: Value to append

        Returns:
            New length of the list
        """
        ...

    async def extend(self, values: list[StateValue]) -> int:
        """
        Extend the list node with multiple values.

        Args:
            values: List of values to append

        Returns:
            New length of the list
        """
        ...

    async def insert(self, index: int, value: StateValue) -> None:
        """
        Insert an item at a specific position in the list node.

        Args:
            index: Position to insert the value
            value: Value to insert

        Raises:
            IndexError: If the index is out of range
        """
        ...

    async def delete(self, index: int) -> None:
        """
        Remove an item from the list node at the specified index.

        Args:
            index: Index of the item to remove

        Raises:
            IndexError: If the index is out of range
        """
        ...

    async def length(self) -> int:
        """
        Get the length of the list node.

        Returns:
            Number of items in the list
        """
        ...

    async def to_list(self) -> list[StateValue]:
        """
        Convert to a regular Python list.

        Returns:
            Python list containing all items from this list node
        """
        ...

    async def clear(self) -> None:
        """
        Remove all items from the list node.
        """
        ...

    async def pop(self, index: int = ...) -> StateValue:
        """
        Remove and return an item from the list node.

        Args:
            index: Index of the item to remove (default: last item)

        Returns:
            The item at the specified index

        Raises:
            IndexError: If the index is out of range
        """
        ...

    async def __len__(self) -> int:
        """
        Get the number of items in the list node.

        Returns:
            The number of items
        """
        ...

    async def __aiter__(self) -> AsyncIterator[StateValue]:
        """
        Get an async iterator over the items.

        Returns:
            Async iterator yielding items
        """
        ...


# --- Protocols for synchronous state handling --- #


class SyncStateNodeProtocol(Protocol):
    """
    Protocol for state tree nodes.

    This abstract base class provides common functionality for both dictionary
    and list state nodes, allowing them to share code for nested node access,
    transformations, filtering, and other common operations.

    SyncStateNodeProtocol serves as a consistent interface for working with nodes,
    regardless of their type (dictionary or list).
    """

    @property
    def path(self) -> StatePath:
        """
        Get the base path for this state node.

        Returns:
            The base path
        """
        ...

    def dict(
        self,
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "SyncTransactionProtocol | None" = None,
    ) -> SyncStateDictProtocol:
        """
        Get a nested dictionary node interface.

        Args:
            path: First path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            A new SyncStateDictProtocol instance for the nested dictionary node
        """
        ...

    def list(
        self,
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "SyncTransactionProtocol | None" = None,
    ) -> SyncStateListProtocol:
        """
        Get a nested list node interface.

        Args:
            path: First path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            A new SyncStateListProtocol instance for the nested list node
        """
        ...

    @overload
    def remove(
        self,
        txn: "SyncTransactionProtocol | None" = None,
    ) -> None: ...

    @overload
    def remove(
        self,
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "SyncTransactionProtocol | None" = None,
    ) -> None: ...

    def remove(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Delete a node from the state tree.

        When called with no path arguments, deletes the current node.
        When called with path segments, deletes the specified nested node.

        Args:
            path: Optional first path segment
            *paths: Additional path segments
            txn: Optional transaction to use
        """
        ...

    @overload
    def exists(
        self,
        txn: "SyncTransactionProtocol | None" = None,
    ) -> bool: ...

    @overload
    def exists(
        self,
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "SyncTransactionProtocol | None" = None,
    ) -> bool: ...

    def exists(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Check if a node exists in the state tree.

        When called with no path arguments, checks if the current node exists.
        When called with path segments, checks if the specified nested node exists.

        Args:
            path: Optional first path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            True if the node exists, False otherwise
        """
        ...

    @overload
    def is_dict(
        self,
        txn: "SyncTransactionProtocol | None" = None,
    ) -> bool: ...

    @overload
    def is_dict(
        self,
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "SyncTransactionProtocol | None" = None,
    ) -> bool: ...

    def is_dict(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Check if a node is a dictionary node.

        When called with no path arguments, checks if the current node is a dictionary.
        When called with path segments, checks if the specified nested node is a dictionary.

        Args:
            path: Optional first path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            True if the node is a dictionary, False otherwise
        """
        ...

    @overload
    def is_list(
        self,
        txn: "SyncTransactionProtocol | None" = None,
    ) -> bool: ...

    @overload
    def is_list(
        self,
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "SyncTransactionProtocol | None" = None,
    ) -> bool: ...

    def is_list(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Check if a node is a list node.

        When called with no path arguments, checks if the current node is a list.
        When called with path segments, checks if the specified nested node is a list.

        Args:
            path: Optional first path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            True if the node is a list, False otherwise
        """
        ...

    @overload
    def to_python_object(
        self,
        txn: "SyncTransactionProtocol | None" = None,
    ) -> StateValue: ...

    @overload
    def to_python_object(
        self,
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "SyncTransactionProtocol | None" = None,
    ) -> StateValue: ...

    def to_python_object(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> StateValue:
        """
        Convert a node to a standard Python object.

        When called with no path arguments, converts the current node.
        When called with path segments, converts the specified nested node.

        Args:
            path: Optional first path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            The Python representation of the node

        Raises:
            KeyError: If the node doesn't exist
        """
        ...

    def copy_to(
        self,
        target: StatePathComponent,
        /,
        *targets: StatePathComponent,
        txn: "SyncTransactionProtocol | None" = None,
    ) -> None:
        """
        Create a copy of this node at another location in the state tree.

        Args:
            target: First segment of the target path
            *targets: Additional segments of the target path
            txn: Optional transaction to use
        """
        ...

    def move_to(
        self,
        target: StatePathComponent,
        /,
        *targets: StatePathComponent,
        txn: "SyncTransactionProtocol | None" = None,
    ) -> None:
        """
        Move this node to another location in the state tree.

        This operation is atomic - either the move completes successfully,
        or no changes are made to the state tree.

        Args:
            target: First segment of the target path
            *targets: Additional segments of the target path
            txn: Optional transaction to use

        Note:
            After this operation, the current SyncStateNodeProtocol instance should not be used
            as its path is no longer valid.
        """
        ...

    @overload
    def transform(
        self,
        transform_func: Callable[[StateValue], StateValue],
        txn: "SyncTransactionProtocol | None" = None,
    ) -> None: ...

    @overload
    def transform(
        self,
        transform_func: Callable[[StateValue], StateValue],
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "SyncTransactionProtocol | None" = None,
    ) -> None: ...

    def transform(
        self,
        transform_func: Callable[[StateValue], StateValue],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Apply a transformation function to a node.

        The transformation function takes the current value as a Python object
        and returns a new transformed Python object.

        When called with just the transform function, transforms the current node.
        When called with path segments, transforms the specified nested node.

        Args:
            transform_func: Function that takes a Python object and returns a transformed version
            path: Optional first path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Raises:
            KeyError: If the node doesn't exist
            TypeError: If the transformation result is not of a compatible type
        """
        ...

    @overload
    def filter(
        self,
        filter_func: Callable[[StateValue], bool] | Callable[[str, StateValue], bool],
        txn: "SyncTransactionProtocol | None" = None,
    ) -> None: ...

    @overload
    def filter(
        self,
        filter_func: Callable[[StateValue], bool] | Callable[[str, StateValue], bool],
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "SyncTransactionProtocol | None" = None,
    ) -> None: ...

    def filter(
        self,
        filter_func: Callable[[StateValue], bool] | Callable[[str, StateValue], bool],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Filter elements of a list or dictionary node.

        For list nodes, filter_func takes (value) and returns a boolean.
        For dictionary nodes, filter_func takes (key, value) and returns a boolean.

        Elements for which filter_func returns False will be removed.

        When called with just the filter function, filters the current node.
        When called with path segments, filters the specified nested node.

        Args:
            filter_func: Function that takes elements and returns whether to keep them
            path: Optional first path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Raises:
            TypeError: If the node is neither a list nor a dictionary
            KeyError: If the node doesn't exist
        """
        ...

    @overload
    def map(
        self,
        map_func: Callable[[StateValue], StateValue],
        txn: "SyncTransactionProtocol | None" = None,
    ) -> None: ...

    @overload
    def map(
        self,
        map_func: Callable[[StateValue], StateValue],
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "SyncTransactionProtocol | None" = None,
    ) -> None: ...

    def map(
        self,
        map_func: Callable[[StateValue], StateValue],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Apply a mapping function to each element in a list or dictionary node.

        For list nodes, each element is replaced with the result of map_func(element).
        For dictionary nodes, each value is replaced with the result of map_func(value).

        This is a convenience method that transforms the node by applying the map function
        to each element while preserving the structure.

        When called with just the map function, maps the current node elements.
        When called with path segments, maps the specified nested node elements.

        Args:
            map_func: Function to apply to each element
            path: Optional first path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Raises:
            TypeError: If the node is neither a list nor a dictionary
            KeyError: If the node doesn't exist
            TypeError: If the mapping result contains unsupported types
        """
        ...

    @overload
    def store(
        self,
        value: StateValue,
        txn: "SyncTransactionProtocol | None" = None,
    ) -> None: ...

    @overload
    def store(
        self,
        value: StateValue,
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "SyncTransactionProtocol | None" = None,
    ) -> None: ...

    def store(
        self,
        value: StateValue,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Store a Python object at a specified node.

        This is a convenience method for directly storing Python objects
        (dictionaries, lists, or primitive values) in the state tree.

        When called with just the value, replaces the current node.
        When called with path segments, stores at the specified nested node.

        Args:
            value: Python object to store
            path: Optional first path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Raises:
            TypeError: If the value is of an unsupported type
        """
        ...


class SyncStateDictProtocol(SyncStateNodeProtocol, Protocol):
    """
    Protocol for dictionary-like interface to state storage.

    This class provides an interface similar to a Python dictionary
    for interacting with dictionary nodes in the state storage.
    It implements methods for dictionary operations that map
    to the underlying state structure.

    Usage:
        # Create or access a dictionary node
        state_dict = state.dict("users", "123")

        # Set values
        state_dict.set("name", "Alice")
        state_dict.set("settings", {"theme": "dark", "notifications": True})

        # Get values
        name = state_dict.get("name")
        theme = state_dict.get("settings", "theme")

        # Delete values
        state_dict.delete("settings")

        # Check if a key exists
        if state_dict.contains("email"):
            email = state_dict.get("email")
    """

    def get(
        self, path: StatePathComponent, /, *paths: StatePathComponent, default: Any = None
    ) -> StateValue:
        """
        Get a value from the dictionary node.

        Args:
            path: First path segment
            *paths: Additional path segments
            default: Value to return if path doesn't exist

        Returns:
            The value associated with the path, or default if not found
        """
        ...

    def set(
        self, path: StatePathComponent, /, *paths: StatePathComponent, value: StateValue
    ) -> None:
        """
        Set a value in the dictionary node.

        Args:
            path: First path segment
            *paths_and_value: Additional path segments followed by the value to set

        Raises:
            ValueError: If no value is provided
        """
        ...

    def delete(self, path: StatePathComponent, /, *paths: StatePathComponent) -> None:
        """
        Delete a path from the dictionary node.

        Args:
            path: First path segment
            *paths: Additional path segments

        Raises:
            KeyError: If the path doesn't exist
        """
        ...

    def contains(self, path: StatePathComponent, /, *paths: StatePathComponent) -> bool:
        """
        Check if a path exists in the dictionary node.

        Args:
            path: First path segment
            *paths: Additional path segments

        Returns:
            True if the path exists, False otherwise
        """
        ...

    def keys(self) -> list[StatePathComponent]:
        """
        Get all top-level keys in the dictionary node.

        Returns:
            List of keys in the dictionary
        """
        ...

    def values(self) -> list[StateValue]:
        """
        Get all top-level values in the dictionary node.

        Returns:
            List of values in the dictionary
        """
        ...

    def items(self) -> list[tuple[StatePathComponent, StateValue]]:
        """
        Get all top-level key-value pairs in the dictionary node.

        Returns:
            List of (key, value) tuples
        """
        ...

    def to_dict(self) -> dict[StatePathComponent, StateValue]:
        """
        Convert to a regular Python dictionary.

        Returns:
            Python dictionary containing all data from this dictionary node
        """
        ...

    def update(self, other: dict[StatePathComponent, StateValue]) -> None:
        """
        Update the dictionary node with key-value pairs from another dictionary.

        Args:
            other: Dictionary containing key-value pairs to update
        """
        ...

    def clear(self) -> None:
        """
        Remove all items from the dictionary node.
        """
        ...

    def pop(self, key: StatePathComponent, default: StateValue = None) -> StateValue:
        """
        Remove and return a value from the dictionary node.

        Args:
            key: Key to remove
            default: Value to return if key doesn't exist

        Returns:
            The value associated with the key, or default if not found

        Raises:
            KeyError: If the key doesn't exist and no default is provided
        """
        ...

    def setdefault(self, key: StatePathComponent, default: StateValue = None) -> StateValue:
        """
        Return the value for key if it exists, otherwise set it to default.

        Args:
            key: Key to check and potentially set
            default: Value to set and return if key doesn't exist

        Returns:
            The value associated with the key, or default if not found
        """
        ...

    def __len__(self) -> int:
        """
        Get the number of items in the dictionary node.

        Returns:
            The number of items
        """
        ...

    def __iter__(self) -> Iterator[StatePathComponent]:
        """
        Get an iterator over the keys.

        Returns:
            Iterator yielding keys
        """
        ...


class SyncStateListProtocol(SyncStateNodeProtocol):
    """
    Protocol for list-like interface to state storage.

    This class provides an interface similar to a Python list
    for interacting with list nodes in the state storage.
    It implements methods for list operations that map
    to the underlying state structure.

    Usage:
        # Create or access a list node
        state_list = state.list("users", "123", "posts")

        # Append items
        state_list.append("New post content")

        # Get items
        first_post = state_list.get(0)

        # Set items
        state_list.set(1, "Updated post content")

        # Remove items
        state_list.delete(2)

        # Get the length
        length = state_list.length()
    """

    def get(self, index: int) -> StateValue:
        """
        Get an item from the list node at the specified index.

        Args:
            index: Index of the item to retrieve

        Returns:
            The item at the specified index

        Raises:
            IndexError: If the index is out of range
        """
        ...

    def set(self, index: int, value: StateValue) -> None:
        """
        Set an item in the list node at the specified index.

        Args:
            index: Index of the item to set
            value: Value to set

        Raises:
            IndexError: If the index is out of range
        """
        ...

    def append(self, value: StateValue) -> int:
        """
        Append an item to the list node.

        Args:
            value: Value to append

        Returns:
            New length of the list
        """
        ...

    def extend(self, values: list[StateValue]) -> int:
        """
        Extend the list node with multiple values.

        Args:
            values: List of values to append

        Returns:
            New length of the list
        """
        ...

    def insert(self, index: int, value: StateValue) -> None:
        """
        Insert an item at a specific position in the list node.

        Args:
            index: Position to insert the value
            value: Value to insert

        Raises:
            IndexError: If the index is out of range
        """
        ...

    def delete(self, index: int) -> None:
        """
        Remove an item from the list node at the specified index.

        Args:
            index: Index of the item to remove

        Raises:
            IndexError: If the index is out of range
        """
        ...

    def length(self) -> int:
        """
        Get the length of the list node.

        Returns:
            Number of items in the list
        """
        ...

    def to_list(self) -> list[StateValue]:
        """
        Convert to a regular Python list.

        Returns:
            Python list containing all items from this list node
        """
        ...

    def clear(self) -> None:
        """
        Remove all items from the list node.
        """
        ...

    def pop(self, index: int = ...) -> StateValue:
        """
        Remove and return an item from the list node.

        Args:
            index: Index of the item to remove (default: last item)

        Returns:
            The item at the specified index

        Raises:
            IndexError: If the index is out of range
        """
        ...

    def __len__(self) -> int:
        """
        Get the number of items in the list node.

        Returns:
            The number of items
        """
        ...

    def __iter__(self) -> Iterator[StateValue]:
        """
        Get an iterator over the items.

        Returns:
            Iterator yielding items
        """
        ...
