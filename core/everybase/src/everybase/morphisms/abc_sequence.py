"""Sequence morphisms — operations (pure) + commands (impure).

Operations:
    FirstOp: First element (seq[0])
    LastOp: Last element (seq[-1])
    IndexOfOp: Find index of value (seq.index(value))
    CountOp: Count occurrences (seq.count(value))

Commands:
    AppendCmd: Append item to end of sequence
    ExtendCmd: Extend sequence with iterable
    InsertCmd: Insert item at index
    PopCmd: Remove and return item at index
    RemoveValueCmd: Remove first occurrence of value
"""

from __future__ import annotations

from collections.abc import Iterable, MutableSequence, Sequence

from everyabc import (
    INVALID,
    BinaryCommand,
    BinaryOperation,
    Sentinel,
    TernaryCommand,
    UnaryOperation,
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
]


# =============================================================================
# OPERATIONS (pure)
# =============================================================================


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


# =============================================================================
# COMMANDS (impure)
# =============================================================================


class AppendCmd[T](BinaryCommand[list[T]]):
    """Append item to end: seq.append(value). Returns mutated list."""

    def apply(self, operand: object, value: object) -> list[T] | Sentinel:
        """Apply."""
        if not isinstance(operand, MutableSequence):
            raise TypeError(f"append() requires mutable sequence, got {type(operand).__name__}")
        operand.append(value)
        return list(operand)  # type: ignore[arg-type]


class InsertCmd[T](TernaryCommand[list[T]]):
    """Insert item at index: seq.insert(index, value). Returns mutated list."""

    def apply(self, operand: object, index: object, value: object) -> list[T] | Sentinel:
        """Apply."""
        if not isinstance(operand, MutableSequence):
            raise TypeError(f"insert() requires mutable sequence, got {type(operand).__name__}")
        if not isinstance(index, int):
            return INVALID
        operand.insert(index, value)
        return list(operand)  # type: ignore[arg-type]


class PopCmd[T](BinaryCommand[T]):
    """Pop item at index: seq.pop(index). Returns popped value.

    Default index is -1 (last item).
    """

    def apply(self, operand: object, index: object) -> T | Sentinel:
        """Apply."""
        if not isinstance(operand, MutableSequence):
            raise TypeError(f"pop() requires mutable sequence, got {type(operand).__name__}")
        if not isinstance(index, int):
            return INVALID
        try:
            return operand.pop(index)  # type: ignore[return-value]
        except IndexError:
            return INVALID


class ExtendCmd[T](BinaryCommand[list[T]]):
    """Extend sequence with iterable: seq.extend(other). Returns mutated list."""

    def apply(self, operand: object, other: object) -> list[T] | Sentinel:
        """Apply."""
        if not isinstance(operand, MutableSequence):
            raise TypeError(f"extend() requires mutable sequence, got {type(operand).__name__}")
        if not isinstance(other, Iterable):
            return INVALID
        operand.extend(other)
        return list(operand)  # type: ignore[arg-type]


class RemoveValueCmd[T](BinaryCommand[list[T]]):
    """Remove first occurrence of value: seq.remove(value). Returns INVALID if not found."""

    def apply(self, operand: object, value: object) -> list[T] | Sentinel:
        """Apply."""
        if not isinstance(operand, MutableSequence):
            raise TypeError(f"remove() requires mutable sequence, got {type(operand).__name__}")
        try:
            operand.remove(value)
        except ValueError:
            return INVALID
        return list(operand)  # type: ignore[arg-type]
