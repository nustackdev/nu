"""Iterable slicing ops — Take, Drop. Lazy iterators."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from itertools import islice
from typing import ClassVar

from nu.terms import INVALID, BinaryQuery, Mode, Sentinel


__all__ = [
    "Drop",
    "Take",
]


class Take(BinaryQuery[Iterator]):
    """Take first N elements: islice(iterable, n) -> lazy iterator."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, left: object, right: object) -> Iterator | Sentinel:
        """Apply: left=iterable, right=n."""
        if not isinstance(left, Iterable):
            raise TypeError(f"Take requires iterable, got {type(left).__name__}")
        try:
            return islice(left, int(right))  # type: ignore
        except (TypeError, ValueError):
            return INVALID


class Drop(BinaryQuery[Iterator]):
    """Drop first N elements: islice(iterable, n, None) -> lazy iterator."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, left: object, right: object) -> Iterator | Sentinel:
        """Apply: left=iterable, right=n."""
        if not isinstance(left, Iterable):
            raise TypeError(f"Drop requires iterable, got {type(left).__name__}")
        try:
            return islice(left, int(right), None)  # type: ignore
        except (TypeError, ValueError):
            return INVALID
