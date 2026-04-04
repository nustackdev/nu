"""Sequence ops — operations (pure) + commands (impure).

Operations:
    FirstOp: First element (seq[0])
    LastOp: Last element (seq[-1])
    IndexOfOp: Find index of value (seq.index(value))
    CountOp: Count occurrences (seq.count(value))
    JoinOp: Join elements into string (sep.join(seq))

Commands:
    AppendCmd: Append item to end of sequence
    ExtendCmd: Extend sequence with iterable
    InsertCmd: Insert item at index
    PopCmd: Remove and return item at index
    RemoveValueCmd: Remove first occurrence of value
"""

from __future__ import annotations

from collections.abc import Iterable, MutableSequence, Sequence

from nu.terms import (
    INVALID,
    BinaryCalc,
    BinaryCmd,
    Sentinel,
    TernaryCmd,
    UnaryCalc,
)


__all__ = [
    "AppendCmd",
    "CountOp",
    "ExtendCmd",
    "FirstOp",
    "IndexOfOp",
    "InsertCmd",
    "JoinOp",
    "LastOp",
    "PopCmd",
    "RemoveValueCmd",
]


# =============================================================================
# OPERATIONS (pure)
# =============================================================================


class FirstOp[ResultT](UnaryCalc[ResultT]):
    """First element: seq[0]. Returns Invalid if empty."""

    def apply(self, operand: object) -> ResultT | Sentinel:
        """Apply."""
        if not isinstance(operand, Sequence):
            raise TypeError(f"first() requires sequence, got {type(operand).__name__}")
        if len(operand) == 0:
            return INVALID
        return operand[0]  # type: ignore


class LastOp[ResultT](UnaryCalc[ResultT]):
    """Last element: seq[-1]. Returns Invalid if empty."""

    def apply(self, operand: object) -> ResultT | Sentinel:
        """Apply."""
        if not isinstance(operand, Sequence):
            raise TypeError(f"last() requires sequence, got {type(operand).__name__}")
        if len(operand) == 0:
            return INVALID
        return operand[-1]  # type: ignore


class IndexOfOp(BinaryCalc[int]):
    """Find index of value: seq.index(value). Returns Invalid if not found."""

    def apply(self, left: object, right: object) -> int | Sentinel:
        """Apply."""
        if not isinstance(left, Sequence):
            raise TypeError(f"index_() requires sequence, got {type(left).__name__}")
        try:
            return left.index(right)
        except ValueError:
            return INVALID


class CountOp(BinaryCalc[int]):
    """Count occurrences: seq.count(value)."""

    def apply(self, left: object, right: object) -> int | Sentinel:
        """Apply."""
        if not isinstance(left, Sequence):
            raise TypeError(f"count_() requires sequence, got {type(left).__name__}")
        return left.count(right)


# =============================================================================
# COMMANDS (impure)
# =============================================================================


class AppendCmd[T](BinaryCmd[None]):
    """Append item to end: seq.append(value). Returns None (mutates in-place)."""

    def apply(self, left: object, right: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(left, MutableSequence):
            raise TypeError(f"append() requires mutable sequence, got {type(left).__name__}")
        left.append(right)
        return None


class InsertCmd[T](TernaryCmd[None]):
    """Insert item at index: seq.insert(index, value). Returns None (mutates in-place)."""

    def apply(self, first: object, second: object, third: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(first, MutableSequence):
            raise TypeError(f"insert() requires mutable sequence, got {type(first).__name__}")
        if not isinstance(second, int):
            return INVALID
        first.insert(second, third)
        return None


class PopCmd[T](BinaryCmd[T]):
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


class ExtendCmd[T](BinaryCmd[None]):
    """Extend sequence with iterable: seq.extend(other). Returns None (mutates in-place)."""

    def apply(self, left: object, right: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(left, MutableSequence):
            raise TypeError(f"extend() requires mutable sequence, got {type(left).__name__}")
        if not isinstance(right, Iterable):
            return INVALID
        left.extend(right)
        return None


class RemoveValueCmd[T](BinaryCmd[None]):
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


# =============================================================================
# JOINING
# =============================================================================


class JoinOp(BinaryCalc[str]):
    """Join elements into string: sep.join(seq)."""

    def apply(self, left: object, right: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(right, str):
            return INVALID
        try:
            return right.join(str(x) for x in left)  # type: ignore
        except TypeError:
            return INVALID
