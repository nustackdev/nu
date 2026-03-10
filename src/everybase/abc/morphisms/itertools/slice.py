"""Iterable slicing morphisms — Take, Drop."""

from __future__ import annotations

from collections.abc import Iterable
from itertools import islice

from everybase.core import INVALID, BinaryOperation, Sentinel


__all__ = [
    "DropOp",
    "TakeOp",
]


class TakeOp(BinaryOperation[list]):
    """Take first N elements: list(islice(iterable, n))."""

    def apply(self, left: object, right: object) -> list | Sentinel:
        """Apply: left=iterable, right=n."""
        if not isinstance(left, Iterable):
            raise TypeError(f"Take requires iterable, got {type(left).__name__}")
        try:
            return list(islice(left, int(right)))  # type: ignore
        except (TypeError, ValueError):
            return INVALID


class DropOp(BinaryOperation[list]):
    """Drop first N elements: list(islice(iterable, n, None))."""

    def apply(self, left: object, right: object) -> list | Sentinel:
        """Apply: left=iterable, right=n."""
        if not isinstance(left, Iterable):
            raise TypeError(f"Drop requires iterable, got {type(left).__name__}")
        try:
            return list(islice(left, int(right), None))  # type: ignore
        except (TypeError, ValueError):
            return INVALID
