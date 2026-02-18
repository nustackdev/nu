"""Collection aggregation morphisms.

SumOp: Sum of elements (sum(seq))
MinOp: Minimum element (min(seq))
MaxOp: Maximum element (max(seq))
AnyOp: Any truthy (any(seq))
AllOp: All truthy (all(seq))
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

from everybase.core import INVALID, Sentinel, UnaryOperation


__all__ = [
    "AllOp",
    "AnyOp",
    "MaxOp",
    "MinOp",
    "SumOp",
]


class SumOp[ResultT](UnaryOperation[ResultT]):
    """Sum of sequence elements: sum(seq)."""

    def apply(self, operand: object) -> ResultT | Sentinel:
        """Apply."""
        if not isinstance(operand, Iterable):
            raise TypeError(f"sum_() requires iterable, got {type(operand).__name__}")
        try:
            return sum(operand)  # type: ignore
        except TypeError:
            return INVALID


class MinOp[ResultT](UnaryOperation[ResultT]):
    """Minimum element: min(seq) or min(seq, key=fn)."""

    def __init__(self, operand: object, key: Callable | None = None) -> None:
        """Initialize."""
        super().__init__(operand)
        self._key = key

    def apply(self, operand: object) -> ResultT | Sentinel:
        """Apply."""
        if not isinstance(operand, Iterable):
            raise TypeError(f"min_() requires iterable, got {type(operand).__name__}")
        try:
            return min(operand, key=self._key)  # type: ignore
        except (TypeError, ValueError):
            return INVALID

    def __repr__(self) -> str:
        if self._key is not None:
            return f"MinOp({self._children[0]!r}, key={self._key!r})"
        return f"MinOp({self._children[0]!r})"


class MaxOp[ResultT](UnaryOperation[ResultT]):
    """Maximum element: max(seq) or max(seq, key=fn)."""

    def __init__(self, operand: object, key: Callable | None = None) -> None:
        """Initialize."""
        super().__init__(operand)
        self._key = key

    def apply(self, operand: object) -> ResultT | Sentinel:
        """Apply."""
        if not isinstance(operand, Iterable):
            raise TypeError(f"max_() requires iterable, got {type(operand).__name__}")
        try:
            return max(operand, key=self._key)  # type: ignore
        except (TypeError, ValueError):
            return INVALID

    def __repr__(self) -> str:
        if self._key is not None:
            return f"MaxOp({self._children[0]!r}, key={self._key!r})"
        return f"MaxOp({self._children[0]!r})"


class AnyOp(UnaryOperation[bool]):
    """Any truthy element: any(seq)."""

    def apply(self, operand: object) -> bool:
        """Apply."""
        if not isinstance(operand, Iterable):
            raise TypeError(f"any_() requires iterable, got {type(operand).__name__}")
        return any(operand)


class AllOp(UnaryOperation[bool]):
    """All truthy elements: all(seq)."""

    def apply(self, operand: object) -> bool:
        """Apply."""
        if not isinstance(operand, Iterable):
            raise TypeError(f"all_() requires iterable, got {type(operand).__name__}")
        return all(operand)
