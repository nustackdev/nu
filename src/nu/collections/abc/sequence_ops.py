"""Sequence ops.

FirstOp, LastOp, IndexOfOp, CountOp
AppendCmd, ExtendCmd, InsertCmd
PopCmd, RemoveValueCmd, ReverseCmd
"""

from __future__ import annotations

from collections.abc import Iterable, MutableSequence, Sequence

from nu.terms import (
    INVALID,
    BinaryOp,
    Sentinel,
    TernaryOp,
    UnaryOp,
)


__all__ = [
    "AppendCmd",
    "CountOp",
    "ExtendCmd",
    "FirstOp",
    "IndexOfOp",
    "InsertCmd",
    "LastOp",
    "PopCmd",
    "RemoveValueCmd",
    "ReverseCmd",
]


# =============================================================================
# SEQUENCE READS
# =============================================================================


class FirstOp[ResultT](UnaryOp[ResultT]):
    """First element: seq[0]. Returns Invalid if empty."""

    def apply(self, operand: object) -> ResultT | Sentinel:
        """Apply."""
        if not isinstance(operand, Sequence):
            raise TypeError(f"first() requires sequence, got {type(operand).__name__}")
        if len(operand) == 0:
            return INVALID
        return operand[0]  # type: ignore


class LastOp[ResultT](UnaryOp[ResultT]):
    """Last element: seq[-1]. Returns Invalid if empty."""

    def apply(self, operand: object) -> ResultT | Sentinel:
        """Apply."""
        if not isinstance(operand, Sequence):
            raise TypeError(f"last() requires sequence, got {type(operand).__name__}")
        if len(operand) == 0:
            return INVALID
        return operand[-1]  # type: ignore


class IndexOfOp(BinaryOp[int]):
    """Find index of value: seq.index(value). Returns Invalid if not found."""

    def apply(self, left: object, right: object) -> int | Sentinel:
        """Apply."""
        if not isinstance(left, Sequence):
            raise TypeError(f"index_() requires sequence, got {type(left).__name__}")
        try:
            return left.index(right)
        except ValueError:
            return INVALID


class CountOp(BinaryOp[int]):
    """Count occurrences: seq.count(value)."""

    def apply(self, left: object, right: object) -> int | Sentinel:
        """Apply."""
        if not isinstance(left, Sequence):
            raise TypeError(f"count_() requires sequence, got {type(left).__name__}")
        return left.count(right)


# =============================================================================
# SEQUENCE MUTATIONS
# =============================================================================


class AppendCmd[T](BinaryOp[None]):
    """Append item to end: seq.append(value). Returns None (mutates in-place)."""

    def apply(self, left: object, right: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(left, MutableSequence):
            raise TypeError(f"append() requires mutable sequence, got {type(left).__name__}")
        left.append(right)
        return None


class InsertCmd[T](TernaryOp[None]):
    """Insert item at index: seq.insert(index, value). Returns None (mutates in-place)."""

    def apply(self, first: object, second: object, third: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(first, MutableSequence):
            raise TypeError(f"insert() requires mutable sequence, got {type(first).__name__}")
        if not isinstance(second, int):
            return INVALID
        first.insert(second, third)
        return None


class PopCmd[T](BinaryOp[T]):
    """Pop item at index: seq.pop(index). Returns popped value.

    Default index is -1 (last item).
    """

    def apply(self, left: object, right: object) -> T | Sentinel:
        """Apply."""
        if not isinstance(left, MutableSequence):
            raise TypeError(f"pop() requires mutable sequence, got {type(left).__name__}")
        if not isinstance(right, int):
            return INVALID
        try:
            return left.pop(right)  # type: ignore[return-value]
        except IndexError:
            return INVALID


class ExtendCmd[T](BinaryOp[None]):
    """Extend sequence with iterable: seq.extend(other). Returns None (mutates in-place)."""

    def apply(self, left: object, right: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(left, MutableSequence):
            raise TypeError(f"extend() requires mutable sequence, got {type(left).__name__}")
        if not isinstance(right, Iterable):
            return INVALID
        left.extend(right)
        return None


class RemoveValueCmd[T](BinaryOp[None]):
    """Remove first occurrence of value: seq.remove(value). Returns None, or INVALID if not found."""

    def apply(self, left: object, right: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(left, MutableSequence):
            raise TypeError(f"remove() requires mutable sequence, got {type(left).__name__}")
        try:
            left.remove(right)
        except ValueError:
            return INVALID
        return None


class ReverseCmd(UnaryOp[None]):
    """Reverse sequence in-place: seq.reverse(). Returns None (mutates in-place)."""

    def apply(self, operand: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(operand, MutableSequence):
            raise TypeError(f"reverse() requires mutable sequence, got {type(operand).__name__}")
        operand.reverse()
        return None
