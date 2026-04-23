"""Sequence ops.

FirstOp, LastOp, IndexOfOp, CountOp
AppendCmd, ExtendCmd, InsertCmd
PopCmd, RemoveValueCmd, ReverseCmd
"""

from __future__ import annotations

from collections.abc import Iterable, MutableSequence, Sequence
from typing import ClassVar

from nu.terms import (
    INVALID,
    BinaryQuery,
    Mode,
    Sentinel,
    TernaryQuery,
    UnaryQuery,
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


class FirstOp[ResultT](UnaryQuery[ResultT]):
    """First element: seq[0]. Returns Invalid if empty."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> ResultT | Sentinel:
        """Apply."""
        if not isinstance(operand, Sequence):
            raise TypeError(f"first() requires sequence, got {type(operand).__name__}")
        if len(operand) == 0:
            return INVALID
        return operand[0]  # type: ignore


class LastOp[ResultT](UnaryQuery[ResultT]):
    """Last element: seq[-1]. Returns Invalid if empty."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> ResultT | Sentinel:
        """Apply."""
        if not isinstance(operand, Sequence):
            raise TypeError(f"last() requires sequence, got {type(operand).__name__}")
        if len(operand) == 0:
            return INVALID
        return operand[-1]  # type: ignore


class IndexOfOp(BinaryQuery[int]):
    """Find index of value: seq.index(value). Returns Invalid if not found."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> int | Sentinel:
        """Apply."""
        if not isinstance(left, Sequence):
            raise TypeError(f"index_() requires sequence, got {type(left).__name__}")
        try:
            return left.index(right)
        except ValueError:
            return INVALID


class CountOp(BinaryQuery[int]):
    """Count occurrences: seq.count(value)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> int | Sentinel:
        """Apply."""
        if not isinstance(left, Sequence):
            raise TypeError(f"count_() requires sequence, got {type(left).__name__}")
        return left.count(right)


# =============================================================================
# SEQUENCE MUTATIONS
# =============================================================================


class AppendCmd[T](BinaryQuery[None]):
    """Append item to end: seq.append(value). Returns None (mutates in-place)."""

    writes = 0
    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(left, MutableSequence):
            raise TypeError(f"append() requires mutable sequence, got {type(left).__name__}")
        left.append(right)
        return None


class InsertCmd[T](TernaryQuery[None]):
    """Insert item at index: seq.insert(index, value). Returns None (mutates in-place)."""

    writes = 0
    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, first: object, second: object, third: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(first, MutableSequence):
            raise TypeError(f"insert() requires mutable sequence, got {type(first).__name__}")
        if not isinstance(second, int):
            return INVALID
        first.insert(second, third)
        return None


class PopCmd[T](BinaryQuery[T]):
    """Pop item at index: seq.pop(index). Returns popped value.

    Default index is -1 (last item).
    """

    writes = 0
    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

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


class ExtendCmd[T](BinaryQuery[None]):
    """Extend sequence with iterable: seq.extend(other). Returns None (mutates in-place)."""

    writes = 0
    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(left, MutableSequence):
            raise TypeError(f"extend() requires mutable sequence, got {type(left).__name__}")
        if not isinstance(right, Iterable):
            return INVALID
        left.extend(right)
        return None


class RemoveValueCmd[T](BinaryQuery[None]):
    """Remove first occurrence of value: seq.remove(value). Returns None, or INVALID if not found."""

    writes = 0
    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(left, MutableSequence):
            raise TypeError(f"remove() requires mutable sequence, got {type(left).__name__}")
        try:
            left.remove(right)
        except ValueError:
            return INVALID
        return None


class ReverseCmd(UnaryQuery[None]):
    """Reverse sequence in-place: seq.reverse(). Returns None (mutates in-place)."""

    writes = 0
    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(operand, MutableSequence):
            raise TypeError(f"reverse() requires mutable sequence, got {type(operand).__name__}")
        operand.reverse()
        return None
