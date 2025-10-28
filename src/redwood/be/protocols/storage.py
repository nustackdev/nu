"""Protocol definitions for coddec, storage, and observer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol


if TYPE_CHECKING:
    from collections.abc import Generator

    from redwood.abc import TupleKey, Value

    from ..types import ScanOptions, StorageDescriptor
    from .codec import CodecProtocol
    from .transaction import (
        SnapshotContextManagerProtocol,
        SnapshotProtocol,
        TransactionContextManagerProtocol,
        TransactionProtocol,
    )


__all__ = [
    "StorageProtocol",
]


class StorageProtocol[EncodedKeyT, EncodedValueT](Protocol):
    """Protocol for state storage adapters."""

    @property
    def codec(self) -> CodecProtocol[EncodedKeyT, EncodedValueT]:
        """Get storage codec for key/value encoding."""
        ...

    def get(self, key: TupleKey) -> Value:
        """Get value by key.

        Args:
            key: State key to retrieve

        Returns:
            State value if found, None otherwise

        Raises:
            StateError: If value cannot be retrieved
        """
        ...

    def set(self, key: TupleKey, value: Value) -> None:
        """Set value by key.

        Args:
            key: State key to set
            value: Value to store

        Raises:
            StateError: If value cannot be stored
        """
        ...

    def delete(self, key: TupleKey) -> None:
        """Delete value by key.

        Args:
            key: State key to delete

        Raises:
            StateError: If value cannot be deleted
        """
        ...

    def exists(self, key: TupleKey) -> bool:
        """Check if key exists.

        Args:
            key: State key to check

        Returns:
            True if key exists, False otherwise

        Raises:
            StateError: If check fails
        """
        ...

    def list_keys(self, prefix: TupleKey, depth: int = ...) -> Generator[TupleKey, None, None]:
        """List all keys under prefix.

        Args:
            prefix: Key prefix to list
            depth: Depth of listing (default is 1)
                If depth is -1, lists all keys under prefix.

        Returns:
            Generator of matching state keys

        Raises:
            StateError: If listing fails
        """
        ...

    def list_values(self, prefix: TupleKey, depth: int = ...) -> Generator[Value, None, None]:
        """List all values under prefix.

        Args:
            prefix: Key prefix to list
            depth: Depth of listing (default is 1)
                If depth is -1, lists all values under prefix.

        Returns:
            Generator of matching state values

        Raises:
            StateError: If listing fails
        """
        ...

    def list_items(
        self,
        prefix: TupleKey,
        depth: int = ...,
    ) -> Generator[tuple[TupleKey, Value], None, None]:
        """List key/value pairs under prefix.

        Args:
            prefix: Key prefix to list
            depth: Depth of listing (default is 1)
                If depth is -1, lists all entries under prefix.

        Returns:
            Generator of matching key/value pairs

        Raises:
            StateError: If listing fails
        """
        ...

    def scan_keys(self, options: ScanOptions, /) -> Generator[TupleKey, None, None]:
        """Perform an ordered scan over keys with fine-grained bounds."""
        ...

    def scan_items(
        self,
        options: ScanOptions,
        /,
    ) -> Generator[tuple[TupleKey, Value], None, None]:
        """Perform an ordered scan yielding key/value pairs."""
        ...

    def begin_transaction(self) -> TransactionProtocol:
        """Begin transaction.

        Returns:
            New transaction instance

        Raises:
            TransactionError: If transaction cannot be started
        """
        ...

    def transaction(self) -> TransactionContextManagerProtocol:
        """Get transaction context manager.

        Returns:
            Transaction context manager
        """
        ...

    def begin_snapshot(self) -> SnapshotProtocol:
        """Begin snapshot.

        Returns:
            New snapshot instance

        Raises:
            StorageError: If snapshot cannot be started
        """
        ...

    def snapshot(self) -> SnapshotContextManagerProtocol:
        """Get snapshot context manager.

        Returns:
            Snapshot context manager
        """
        ...

    def describe(self) -> StorageDescriptor:
        """Return capability and configuration metadata for this storage."""
        ...

    def __hash__(self) -> int:
        """Get hash of the storage.

        Returns:
            Hash value of the storage
        """
        ...

    def __eq__(self, other: object) -> bool:
        """Check equality of the storage.

        Args:
            other: Value to compare with

        Returns:
            True if equal, False otherwise
        """
        ...
