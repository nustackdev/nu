"""Context protocol definitions for unified transaction and snapshot handling."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Union, runtime_checkable


if TYPE_CHECKING:
    from collections.abc import Generator

    from ..types import PathTuple, Value


__all__ = [
    "ContextProtocol",
    "ContextType",
    "SnapshotContextProtocol",
    "TransactionContextProtocol",
]


@runtime_checkable
class ContextProtocol(Protocol):
    """Base context protocol for read-only operations.

    This protocol defines the minimal interface that both transactions
    and snapshots must support for read operations.
    """

    def get(self, key: PathTuple) -> Value:
        """Get value for key."""
        ...

    def exists(self, key: PathTuple) -> bool:
        """Check if key exists."""
        ...

    def list_keys(self, prefix: PathTuple, depth: int = 1) -> Generator[PathTuple, None, None]:
        """List keys with given prefix and depth."""
        ...


@runtime_checkable
class TransactionContextProtocol(ContextProtocol, Protocol):
    """Transaction context protocol extending base context with write operations.

    Transactions support both read and write operations and provide
    commit/rollback semantics for atomicity.
    """

    def set(self, key: PathTuple, value: Value) -> None:
        """Set value for key."""
        ...

    def delete(self, key: PathTuple) -> None:
        """Delete key."""
        ...

    def commit(self) -> None:
        """Commit transaction changes."""
        ...

    def rollback(self) -> None:
        """Rollback transaction changes."""
        ...


@runtime_checkable
class SnapshotContextProtocol(ContextProtocol, Protocol):
    """Snapshot context protocol for read-only operations with cleanup.

    Snapshots provide consistent read-only views of data and require
    explicit cleanup when no longer needed.
    """

    def close(self) -> None:
        """Close snapshot and release resources."""
        ...


# Union type for context attributes
ContextType = Union[TransactionContextProtocol, SnapshotContextProtocol]
