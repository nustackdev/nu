"""Iterable reduction ops — terminal operations that consume iterables.

Sum: Sum of elements (sum(seq))
Min: Minimum element (min(seq))
Max: Maximum element (max(seq))
Any: Any truthy (any(seq))
All: All truthy (all(seq))
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import ClassVar

from nu.terms import INVALID, Mode, Sentinel, UnaryQuery


__all__ = [
    "All",
    "Any",
    "Max",
    "Min",
    "Sum",
]


class Sum[ResultT](UnaryQuery[ResultT]):
    """Sum of sequence elements: sum(seq)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> ResultT | Sentinel:
        """Apply."""
        if not isinstance(operand, Iterable):
            raise TypeError(f"sum_() requires iterable, got {type(operand).__name__}")
        try:
            return sum(operand)  # type: ignore
        except TypeError:
            return INVALID


class Min[ResultT](UnaryQuery[ResultT]):
    """Minimum element: min(seq)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> ResultT | Sentinel:
        """Apply."""
        if not isinstance(operand, Iterable):
            raise TypeError(f"min_() requires iterable, got {type(operand).__name__}")
        try:
            return min(operand)  # type: ignore
        except (TypeError, ValueError):
            return INVALID


class Max[ResultT](UnaryQuery[ResultT]):
    """Maximum element: max(seq)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> ResultT | Sentinel:
        """Apply."""
        if not isinstance(operand, Iterable):
            raise TypeError(f"max_() requires iterable, got {type(operand).__name__}")
        try:
            return max(operand)  # type: ignore
        except (TypeError, ValueError):
            return INVALID


class Any(UnaryQuery[bool]):
    """Any truthy element: any(seq)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> bool:
        """Apply."""
        if not isinstance(operand, Iterable):
            raise TypeError(f"any_() requires iterable, got {type(operand).__name__}")
        return any(operand)


class All(UnaryQuery[bool]):
    """All truthy elements: all(seq)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> bool:
        """Apply."""
        if not isinstance(operand, Iterable):
            raise TypeError(f"all_() requires iterable, got {type(operand).__name__}")
        return all(operand)
