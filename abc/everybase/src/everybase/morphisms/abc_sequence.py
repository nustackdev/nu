"""Sequence ABC morphisms.

FirstOp: First element (seq[0])
LastOp: Last element (seq[-1])
IndexOfOp: Find index of value (seq.index(value))
CountOp: Count occurrences (seq.count(value))
"""

from __future__ import annotations

from collections.abc import Sequence

from everyabc import INVALID, BinaryOperation, Sentinel, UnaryOperation


__all__ = [
    "CountOp",
    "FirstOp",
    "IndexOfOp",
    "LastOp",
]


class FirstOp[ResultT](UnaryOperation[ResultT]):
    """First element: seq[0]. Returns Invalid if empty."""

    def apply(self, operand: object) -> ResultT | Sentinel:
        """Apply."""
        if not isinstance(operand, Sequence):
            raise TypeError(f"first() requires sequence, got {type(operand).__name__}")
        if len(operand) == 0:
            return INVALID
        return operand[0]  # type: ignore


class LastOp[ResultT](UnaryOperation[ResultT]):
    """Last element: seq[-1]. Returns Invalid if empty."""

    def apply(self, operand: object) -> ResultT | Sentinel:
        """Apply."""
        if not isinstance(operand, Sequence):
            raise TypeError(f"last() requires sequence, got {type(operand).__name__}")
        if len(operand) == 0:
            return INVALID
        return operand[-1]  # type: ignore


class IndexOfOp(BinaryOperation[int]):
    """Find index of value: seq.index(value). Returns Invalid if not found."""

    def apply(self, left: object, right: object) -> int | Sentinel:
        """Apply."""
        if not isinstance(left, Sequence):
            raise TypeError(f"index_() requires sequence, got {type(left).__name__}")
        try:
            return left.index(right)
        except ValueError:
            return INVALID


class CountOp(BinaryOperation[int]):
    """Count occurrences: seq.count(value)."""

    def apply(self, left: object, right: object) -> int | Sentinel:
        """Apply."""
        if not isinstance(left, Sequence):
            raise TypeError(f"count_() requires sequence, got {type(left).__name__}")
        return left.count(right)
