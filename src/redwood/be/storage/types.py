"""Storage type definitions.

Defines data structures and type aliases used across the storage layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Callable

    from redwood.abc import TupleKey, Value


@dataclass(frozen=True, kw_only=True)
class ScanOptions:
    """Options for range scan operations.

    Defines the bounds, direction, and limits for iterating over key ranges.

    Attributes:
        start: Starting key (inclusive by default). None means from beginning.
        end: Ending key (exclusive by default). None means to end.
        start_inclusive: Whether start key is inclusive.
        end_inclusive: Whether end key is inclusive.
        direction: Direction to scan (forward or reverse).
        limit: Maximum number of results. None means unlimited.
    """

    start: TupleKey | None = None
    end: TupleKey | None = None
    start_inclusive: bool = True
    end_inclusive: bool = False
    reverse: bool = False
    limit: int | None = None


# Type alias for subscription handles
type SubscriptionHandle = int | str


# Type alias for subscription callbacks
type SubscriptionCallback = Callable[[TupleKey, Value], None]


__all__ = [
    "ScanOptions",
    "SubscriptionCallback",
    "SubscriptionHandle",
]
