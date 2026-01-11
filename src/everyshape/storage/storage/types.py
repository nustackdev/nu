"""Storage type definitions.

Defines data structures and type aliases used across the storage layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from everyshape.loc import key

    from ..filter import Filter
    from .transaction import SnapshotProtocol, TransactionProtocol, WriteBatchProtocol


@dataclass(frozen=True, kw_only=True)
class StorageScanOptions:
    """Options for range scan operations.

    Defines the starting position, direction, limits, and filtering
    for iterating over key ranges.

    Attributes:
        start: Starting key (inclusive). None means from beginning.
        reverse: If True, scan in reverse order.
        limit: Maximum number of results. None means unlimited.
        filter: Filter to include keys (skip if not matched).
        break_filter: Filter to break iteration (stop when not matched).
            Used for efficient prefix scans - break when past prefix range.

    Filter vs break_filter:
        - filter: If key doesn't match, SKIP it (continue to next)
        - break_filter: If key doesn't match, STOP iteration entirely

    Examples:
        >>> # Scan all keys starting from ("users",)
        >>> options = StorageScanOptions(start=("users",))

        >>> # Scan with prefix filter (efficient - breaks when past prefix)
        >>> from everyshape.storage.filter import PrefixFilter, LengthFilter
        >>> options = StorageScanOptions(
        ...     start=("users",),
        ...     break_filter=PrefixFilter(prefix=("users",)),
        ...     filter=LengthFilter(length=3),  # only length-3 keys
        ... )

        >>> # Scan children: prefix + length filter
        >>> options = StorageScanOptions(
        ...     start=("users",),
        ...     break_filter=PrefixFilter(prefix=("users",)),
        ...     filter=PrefixFilter(prefix=("users",)) & LengthFilter(length=2),
        ... )
    """

    start: key.Key | None = None
    reverse: bool = False
    limit: int | None = None
    filter: Filter | None = None
    break_filter: Filter | None = None


type StorageContextType = SnapshotProtocol | WriteBatchProtocol | TransactionProtocol


__all__ = [
    "StorageContextType",
    "StorageScanOptions",
]
