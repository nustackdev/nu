"""Iterable reduction ops — terminal operations that consume iterables.

Sum: Sum of elements (sum(seq))
Min: Minimum element (min(seq))
Max: Maximum element (max(seq))
Any: Any truthy (any(seq))
All: All truthy (all(seq))
"""

from __future__ import annotations

from collections.abc import Iterable

from nu.terms import INVALID, Sentinel, UnaryScalar


__all__ = [
    "All",
    "Any",
    "Max",
    "Min",
    "Sum",
]


class Sum[ResultT](UnaryScalar[ResultT]):
    """Sum of sequence elements: sum(seq)."""

    def apply(self, operand: object) -> ResultT | Sentinel:
        """Apply."""
        if not isinstance(operand, Iterable):
            raise TypeError(f"sum_() requires iterable, got {type(operand).__name__}")
        try:
            return sum(operand)  # type: ignore
        except TypeError:
            return INVALID


class Min[ResultT](UnaryScalar[ResultT]):
    """Minimum element: min(seq)."""

    def apply(self, operand: object) -> ResultT | Sentinel:
        """Apply."""
        if not isinstance(operand, Iterable):
            raise TypeError(f"min_() requires iterable, got {type(operand).__name__}")
        try:
            return min(operand)  # type: ignore
        except (TypeError, ValueError):
            return INVALID


class Max[ResultT](UnaryScalar[ResultT]):
    """Maximum element: max(seq)."""

    def apply(self, operand: object) -> ResultT | Sentinel:
        """Apply."""
        if not isinstance(operand, Iterable):
            raise TypeError(f"max_() requires iterable, got {type(operand).__name__}")
        try:
            return max(operand)  # type: ignore
        except (TypeError, ValueError):
            return INVALID


class Any(UnaryScalar[bool]):
    """Any truthy element: any(seq)."""

    def apply(self, operand: object) -> bool:
        """Apply."""
        if not isinstance(operand, Iterable):
            raise TypeError(f"any_() requires iterable, got {type(operand).__name__}")
        return any(operand)


class All(UnaryScalar[bool]):
    """All truthy elements: all(seq)."""

    def apply(self, operand: object) -> bool:
        """Apply."""
        if not isinstance(operand, Iterable):
            raise TypeError(f"all_() requires iterable, got {type(operand).__name__}")
        return all(operand)
