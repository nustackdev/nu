from __future__ import annotations

from contextlib import AbstractAsyncContextManager, AbstractContextManager
from typing import TYPE_CHECKING, AsyncGenerator, Callable, Generator, Protocol, runtime_checkable

from .kv import (
    AsyncTransactionContextManagerProtocol,
    AsyncTransactionProtocol,
    SyncTransactionContextManagerProtocol,
    SyncTransactionProtocol,
)
from .observer import AsyncSubscriptionProtocol, SyncSubscriptionProtocol
from .types import TreePathComponent, Value

if TYPE_CHECKING:
    pass

__all__ = [
    "EmptyProtocol",
    "SyncStateProtocol",
    "SyncBaseViewProtocol",
    "SyncDictViewProtocol",
    "SyncListViewProtocol",
    "AsyncStateProtocol",
    "AsyncBaseViewProtocol",
    "AsyncDictViewProtocol",
    "AsyncListViewProtocol",
]


class EmptyProtocol(Protocol):
    """Placeholder class representing an empty value."""

    pass


class PathProtocol(Protocol):
    def to_tuple(self) -> tuple[TreePathComponent, ...]:
        """Convert the path to a tuple of components."""
        ...


# --- Synchronous Protocols ---


@runtime_checkable
class SyncStateProtocol(Protocol):
    """Protocol for synchronous state tree navigation and management."""

    @property
    def is_sync(self) -> bool:
        """Check if the protocol is synchronous."""
        return True

    @property
    def path(self) -> PathProtocol:
        """Get the current path in the state tree."""
        ...

    def at(
        self, *paths: TreePathComponent, tx: SyncTransactionProtocol | None = None
    ) -> "SyncStateProtocol":
        """Navigate to a path relative to current path."""
        ...

    def parent(self, *, tx: SyncTransactionProtocol | None = None) -> "SyncStateProtocol":
        """Navigate to parent path."""
        ...

    def root(self, *, tx: SyncTransactionProtocol | None = None) -> "SyncStateProtocol":
        """Navigate to root path."""
        ...

    def with_dict_view(self) -> AbstractContextManager["SyncDictViewProtocol"]:
        """Access container as dictionary view with automatic transaction management."""
        ...

    def with_list_view(self) -> AbstractContextManager["SyncListViewProtocol"]:
        """Access container as list view with automatic transaction management."""
        ...

    def dict_view(self, *, tx: SyncTransactionProtocol | None = None) -> "SyncDictViewProtocol":
        """Access container as dictionary view with manual transaction management."""
        ...

    def list_view(self, *, tx: SyncTransactionProtocol | None = None) -> "SyncListViewProtocol":
        """Access container as list view with manual transaction management."""
        ...

    def begin_transaction(self) -> SyncTransactionProtocol:
        """Start a new transaction."""
        ...

    def transaction(self) -> SyncTransactionContextManagerProtocol:
        """Get transaction context manager for combined storage and notification handling."""
        ...

    def subscribe(self, callback: Callable, depth: int = 0) -> SyncSubscriptionProtocol:
        """Subscribe to changes at the current path."""
        ...

    def unsubscribe(self, subscription: SyncSubscriptionProtocol) -> None:
        """Unsubscribe from changes."""
        ...

    def has_primitive(self, *paths: TreePathComponent) -> bool:
        """
        Check if a path exists.

        Args:
            *paths: Path components to check

        Returns:
            bool: True if path exists, False otherwise

        Example:
            ```python
            if tree.at("users").has("alice"):
                print("Alice exists")
            else:
                print("Alice does not exist")
            ```
        """
        ...

    def get_primitive(
        self, *paths: TreePathComponent, default: Value | EmptyProtocol = ...
    ) -> Value | EmptyProtocol:
        """
        Get value at a path.

        Args:
            *paths: Path components to get
            default: Default value if path does not exist

        Returns:
            Value at the path, or default if not found

        Example:
            ```python
            email = tree.at("users", "alice").get("email", default="not found")
            if email is None:
                print("Alice's email not found")
            else:
                print(f"Alice's email: {email}")
            ```
        """
        ...

    def is_primitive(self, *paths: TreePathComponent) -> bool:
        """
        Check if a path is a primitive (non-container).

        Args:
            *paths: Path components to check

        Returns:
            bool: True if path is a primitive, False otherwise

        Example:
            ```python
            if tree.at("users").is_primitive("alice", "email"):
                print("Alice's email is a primitive value")
            else:
                print("Alice's email is not a primitive value")
            ```
        """
        ...

    def is_container(self, *paths: TreePathComponent) -> bool:
        """
        Check if a path is a container (mapping, indexed, linked, or hashed).

        Args:
            *paths: Path components to check

        Returns:
            bool: True if path is a container, False otherwise

        Example:
            ```python
            if tree.at("users").is_container("alice"):
                print("Alice's profile is a container")
            else:
                print("Alice's profile is not a container")
            ```
        """
        ...

    def is_mapping(self, *paths: TreePathComponent) -> bool:
        """
        Check if a path is a mapping (dictionary-like).

        Args:
            *paths: Path components to check

        Returns:
            bool: True if path is a mapping, False otherwise

        Example:
            ```python
            if tree.at("users").is_mapping("alice"):
                print("Alice's profile is a mapping")
            else:
                print("Alice's profile is not a mapping")
            ```
        """
        ...

    def is_indexed(self, *paths: TreePathComponent) -> bool:
        """
        Check if a path is an indexed container (list-like).

        Args:
            *paths: Path components to check

        Returns:
            bool: True if path is an indexed container, False otherwise

        Example:
            ```python
            if tree.at("tasks").is_indexed():
                print("Tasks is an indexed container")
            else:
                print("Tasks is not an indexed container")
            ```
        """
        ...

    def is_linked(self, *paths: TreePathComponent) -> bool:
        """
        Check if a path is a linked container (set-like).

        Args:
            *paths: Path components to check

        Returns:
            bool: True if path is a linked container, False otherwise

        Example:
            ```python
            if tree.at("tags").is_linked():
                print("Tags is a linked container")
            else:
                print("Tags is not a linked container")
            ```
        """
        ...

    def is_hashed(self, *paths: TreePathComponent) -> bool:
        """
        Check if a path is a hashed container (hash-like).

        Args:
            *paths: Path components to check

        Returns:
            bool: True if path is a hashed container, False otherwise

        Example:
            ```python
            if tree.at("users").is_hashed():
                print("Users is a hashed container")
            else:
                print("Users is not a hashed container")
            ```
        """
        ...


@runtime_checkable
class SyncBaseViewProtocol(Protocol):
    """Base protocol for synchronous view implementations."""

    def at(
        self, *paths: TreePathComponent, tx: SyncTransactionProtocol | None = None
    ) -> SyncStateProtocol:
        """Navigate to a path relative to current path."""
        ...

    def parent(self, *, tx: SyncTransactionProtocol | None = None) -> SyncStateProtocol:
        """Navigate to parent path."""
        ...

    def root(self, *, tx: SyncTransactionProtocol | None = None) -> SyncStateProtocol:
        """Navigate to root path."""
        ...

    def store(self, value: Value, /, *, replace: bool = False) -> None:
        """Store value in the view."""
        ...

    def extract(self) -> Value | EmptyProtocol:
        """Extract value from the view."""
        ...


@runtime_checkable
class SyncDictViewProtocol(SyncBaseViewProtocol, Protocol):
    """Protocol for synchronous dictionary view interface."""

    def get(
        self, key: TreePathComponent, default: Value | EmptyProtocol = ...
    ) -> Value | EmptyProtocol:
        """Get value at key."""
        ...

    def set(self, key: TreePathComponent, value: Value) -> None:
        """Set value at key."""
        ...

    def has(self, key: TreePathComponent) -> bool:
        """Check if key exists in the container."""
        ...

    def remove(self, key: TreePathComponent) -> bool:
        """Remove key from the container."""
        ...

    def clear(self) -> int:
        """Remove all items from the container."""
        ...

    def keys(self) -> Generator[TreePathComponent, None, None]:
        """Get all keys in the container."""
        ...

    def values(self) -> Generator[Value, None, None]:
        """Get all values in the container."""
        ...

    def items(self) -> Generator[tuple[TreePathComponent, Value], None, None]:
        """Get all key-value pairs in the container."""
        ...

    def dict_view(self, key: TreePathComponent) -> "SyncDictViewProtocol":
        """Get a dictionary view for a nested container."""
        ...

    def list_view(self, key: TreePathComponent) -> "SyncListViewProtocol":
        """Get a list view for a nested container."""
        ...


@runtime_checkable
class SyncListViewProtocol(SyncBaseViewProtocol, Protocol):
    """Protocol for synchronous list view interface."""

    def length(self) -> int:
        """Get the length of the list."""
        ...

    def get(self, index: int, default: Value | EmptyProtocol = ...) -> Value | EmptyProtocol:
        """Get value at index."""
        ...

    def append(self, value: Value) -> None:
        """Append value to the end of the list."""
        ...

    def pop(self) -> Value:
        """Remove and return the last item."""
        ...

    def extend(self, iterable) -> None:
        """Extend list by appending elements from iterable."""
        ...

    def clear(self) -> None:
        """Remove all items from the list."""
        ...

    def values(self) -> Generator[Value, None, None]:
        """Get all values in the list."""
        ...

    def dict_view(self, index: int) -> SyncDictViewProtocol:
        """Get a dictionary view for a nested container at index."""
        ...

    def list_view(self, index: int) -> "SyncListViewProtocol":
        """Get a list view for a nested container at index."""
        ...


# --- Asynchronous Protocols ---


@runtime_checkable
class AsyncStateProtocol(Protocol):
    """Protocol for asynchronous state tree navigation and management."""

    @property
    def is_async(self) -> bool:
        """Check if the protocol is asynchronous."""
        return True

    @property
    def path(self) -> PathProtocol:
        """Get the current path in the state tree."""
        ...

    async def at(
        self, *paths: TreePathComponent, tx: AsyncTransactionProtocol | None = None
    ) -> "AsyncStateProtocol":
        """Navigate to a path relative to current path."""
        ...

    async def parent(self, *, tx: AsyncTransactionProtocol | None = None) -> "AsyncStateProtocol":
        """Navigate to parent path."""
        ...

    async def root(self, *, tx: AsyncTransactionProtocol | None = None) -> "AsyncStateProtocol":
        """Navigate to root path."""
        ...

    async def with_dict_view(self) -> AbstractAsyncContextManager["AsyncDictViewProtocol"]:
        """Access container as dictionary view with automatic transaction management."""
        ...

    async def with_list_view(self) -> AbstractAsyncContextManager["AsyncListViewProtocol"]:
        """Access container as list view with automatic transaction management."""
        ...

    async def dict_view(
        self, *, tx: AsyncTransactionProtocol | None = None
    ) -> "AsyncDictViewProtocol":
        """Access container as dictionary view with manual transaction management."""
        ...

    async def list_view(
        self, *, tx: AsyncTransactionProtocol | None = None
    ) -> "AsyncListViewProtocol":
        """Access container as list view with manual transaction management."""
        ...

    async def begin_transaction(self) -> AsyncTransactionProtocol:
        """Start a new transaction."""
        ...

    async def transaction(self) -> AsyncTransactionContextManagerProtocol:
        """Get transaction context manager for combined storage and notification handling."""
        ...

    async def subscribe(self, callback: Callable, depth: int = 0) -> AsyncSubscriptionProtocol:
        """Subscribe to changes at the current path."""
        ...

    async def unsubscribe(self, subscription: AsyncSubscriptionProtocol) -> None:
        """Unsubscribe from changes."""
        ...

    async def exists(self, *paths: TreePathComponent) -> bool:
        """Check if a path exists in the state tree."""
        ...

    async def get(
        self, *paths: TreePathComponent, default: Value | EmptyProtocol = ...
    ) -> Value | EmptyProtocol:
        """Get value at a path."""
        ...

    async def has_primitive(self, *paths: TreePathComponent) -> bool:
        """
        Check if a path exists.

        Args:
            *paths: Path components to check

        Returns:
            bool: True if path exists, False otherwise

        Example:
            ```python
            if tree.at("users").has("alice"):
                print("Alice exists")
            else:
                print("Alice does not exist")
            ```
        """
        ...

    async def get_primitive(
        self, *paths: TreePathComponent, default: Value | EmptyProtocol = ...
    ) -> Value | EmptyProtocol:
        """
        Get value at a path.

        Args:
            *paths: Path components to get
            default: Default value if path does not exist

        Returns:
            Value at the path, or default if not found

        Example:
            ```python
            email = tree.at("users", "alice").get("email", default="not found")
            if email is None:
                print("Alice's email not found")
            else:
                print(f"Alice's email: {email}")
            ```
        """
        ...

    async def is_primitive(self, *paths: TreePathComponent) -> bool:
        """
        Check if a path is a primitive (non-container).

        Args:
            *paths: Path components to check

        Returns:
            bool: True if path is a primitive, False otherwise

        Example:
            ```python
            if tree.at("users").is_primitive("alice", "email"):
                print("Alice's email is a primitive value")
            else:
                print("Alice's email is not a primitive value")
            ```
        """
        ...

    async def is_container(self, *paths: TreePathComponent) -> bool:
        """
        Check if a path is a container (mapping, indexed, linked, or hashed).

        Args:
            *paths: Path components to check

        Returns:
            bool: True if path is a container, False otherwise

        Example:
            ```python
            if tree.at("users").is_container("alice"):
                print("Alice's profile is a container")
            else:
                print("Alice's profile is not a container")
            ```
        """
        ...

    async def is_mapping(self, *paths: TreePathComponent) -> bool:
        """
        Check if a path is a mapping (dictionary-like).

        Args:
            *paths: Path components to check

        Returns:
            bool: True if path is a mapping, False otherwise

        Example:
            ```python
            if tree.at("users").is_mapping("alice"):
                print("Alice's profile is a mapping")
            else:
                print("Alice's profile is not a mapping")
            ```
        """
        ...

    async def is_indexed(self, *paths: TreePathComponent) -> bool:
        """
        Check if a path is an indexed container (list-like).

        Args:
            *paths: Path components to check

        Returns:
            bool: True if path is an indexed container, False otherwise

        Example:
            ```python
            if tree.at("tasks").is_indexed():
                print("Tasks is an indexed container")
            else:
                print("Tasks is not an indexed container")
            ```
        """
        ...

    async def is_linked(self, *paths: TreePathComponent) -> bool:
        """
        Check if a path is a linked container (set-like).

        Args:
            *paths: Path components to check

        Returns:
            bool: True if path is a linked container, False otherwise

        Example:
            ```python
            if tree.at("tags").is_linked():
                print("Tags is a linked container")
            else:
                print("Tags is not a linked container")
            ```
        """
        ...

    async def is_hashed(self, *paths: TreePathComponent) -> bool:
        """
        Check if a path is a hashed container (hash-like).

        Args:
            *paths: Path components to check

        Returns:
            bool: True if path is a hashed container, False otherwise

        Example:
            ```python
            if tree.at("users").is_hashed():
                print("Users is a hashed container")
            else:
                print("Users is not a hashed container")
            ```
        """
        ...


@runtime_checkable
class AsyncBaseViewProtocol(Protocol):
    """Base protocol for asynchronous view implementations."""

    async def at(
        self, *paths: TreePathComponent, tx: AsyncTransactionProtocol | None = None
    ) -> AsyncStateProtocol:
        """Navigate to a path relative to current path."""
        ...

    async def parent(self, *, tx: AsyncTransactionProtocol | None = None) -> AsyncStateProtocol:
        """Navigate to parent path."""
        ...

    async def root(self, *, tx: AsyncTransactionProtocol | None = None) -> AsyncStateProtocol:
        """Navigate to root path."""
        ...

    async def store(self, value: Value, /, *, replace: bool = False) -> None:
        """Store value in the view."""
        ...

    async def extract(self) -> Value | EmptyProtocol:
        """Extract value from the view."""
        ...


@runtime_checkable
class AsyncDictViewProtocol(AsyncBaseViewProtocol, Protocol):
    """Protocol for asynchronous dictionary view interface."""

    async def get(
        self, key: TreePathComponent, default: Value | EmptyProtocol = ...
    ) -> Value | EmptyProtocol:
        """Get value at key."""
        ...

    async def set(self, key: TreePathComponent, value: Value) -> None:
        """Set value at key."""
        ...

    async def has(self, key: TreePathComponent) -> bool:
        """Check if key exists in the container."""
        ...

    async def remove(self, key: TreePathComponent) -> bool:
        """Remove key from the container."""
        ...

    async def clear(self) -> int:
        """Remove all items from the container."""
        ...

    async def keys(self) -> AsyncGenerator[TreePathComponent, None]:
        """Get all keys in the container."""
        ...

    async def values(self) -> AsyncGenerator[Value, None]:
        """Get all values in the container."""
        ...

    async def items(self) -> AsyncGenerator[tuple[TreePathComponent, Value], None]:
        """Get all key-value pairs in the container."""
        ...

    async def dict_view(self, key: TreePathComponent) -> "AsyncDictViewProtocol":
        """Get a dictionary view for a nested container."""
        ...

    async def list_view(self, key: TreePathComponent) -> "AsyncListViewProtocol":
        """Get a list view for a nested container."""
        ...


@runtime_checkable
class AsyncListViewProtocol(AsyncBaseViewProtocol, Protocol):
    """Protocol for asynchronous list view interface."""

    async def length(self) -> int:
        """Get the length of the list."""
        ...

    async def get(self, index: int, default: Value | EmptyProtocol = ...) -> Value | EmptyProtocol:
        """Get value at index."""
        ...

    async def append(self, value: Value) -> None:
        """Append value to the end of the list."""
        ...

    async def pop(self) -> Value:
        """Remove and return the last item."""
        ...

    async def extend(self, iterable) -> None:
        """Extend list by appending elements from iterable."""
        ...

    async def clear(self) -> None:
        """Remove all items from the list."""
        ...

    async def values(self) -> AsyncGenerator[Value, None]:
        """Get all values in the list."""
        ...

    async def dict_view(self, index: int) -> AsyncDictViewProtocol:
        """Get a dictionary view for a nested container at index."""
        ...

    async def list_view(self, index: int) -> "AsyncListViewProtocol":
        """Get a list view for a nested container at index."""
        ...
