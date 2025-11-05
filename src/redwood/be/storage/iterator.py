"""Storage protocol definitions.

Defines the abstract interfaces for storage operations, transactions,
and iteration. Implementations must conform to these protocols.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable


if TYPE_CHECKING:
    from types import TracebackType

    from redwood.abc import TupleKey, Value


@runtime_checkable
class IteratorProtocol(Protocol):
    """Low-level iterator interface for range scans.

    Provides cursor-like navigation over key ranges with bidirectional
    movement and positioning. Similar to LMDB cursors or RocksDB iterators.
    """

    def seek(self, key: TupleKey) -> bool:
        """Seek to key position.

        Args:
            key: Key to seek to.

        Returns:
            True if positioned successfully, False otherwise.
        """
        ...

    def seek_to_first(self) -> bool:
        """Seek to first key.

        Returns:
            True if positioned successfully, False if empty.
        """
        ...

    def seek_to_last(self) -> bool:
        """Seek to last key.

        Returns:
            True if positioned successfully, False if empty.
        """
        ...

    def next(self) -> bool:
        """Move to next key.

        Returns:
            True if moved successfully, False if at end.
        """
        ...

    def prev(self) -> bool:
        """Move to previous key.

        Returns:
            True if moved successfully, False if at beginning.
        """
        ...

    def key(self) -> TupleKey:
        """Get current key.

        Returns:
            Current key at iterator position.

        Raises:
            StorageIteratorError: If iterator is not valid.
        """
        ...

    def value(self) -> Value:
        """Get current value.

        Returns:
            Current value at iterator position.

        Raises:
            StorageIteratorError: If iterator is not valid.
        """
        ...

    def is_valid(self) -> bool:
        """Check if iterator is positioned at valid data.

        Returns:
            True if positioned at valid key/value, False otherwise.
        """
        ...

    def close(self) -> None:
        """Close iterator and release resources."""
        ...

    def __enter__(self) -> IteratorProtocol:
        """Enter context manager."""
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit context manager and close iterator."""
        ...


__all__ = [
    "IteratorProtocol",
]
