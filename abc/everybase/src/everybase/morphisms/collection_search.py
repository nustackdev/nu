"""Collection search morphisms.

FirstOp: First element (seq[0])
LastOp: Last element (seq[-1])
IndexOfOp: Find index of value (seq.index(value))
FindOp: Find first element matching predicate
FindIndexOp: Find index of first element matching predicate
CountOp: Count occurrences (seq.count(value))
JoinOp: Join strings (sep.join(seq))
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everyabc import INVALID, BinaryMorphism, NAryMorphism, Operation, Sentinel, UnaryMorphism


if TYPE_CHECKING:
    from collections.abc import Callable


__all__ = [
    "CountOp",
    "FindIndexOp",
    "FindOp",
    "FirstOp",
    "IndexOfOp",
    "JoinOp",
    "LastOp",
]


class FirstOp[ResultT](Operation, UnaryMorphism[ResultT | Sentinel]):
    """First element: seq[0]. Returns Invalid if empty."""

    def _apply(self, operand: object) -> ResultT | Sentinel:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"first() requires list or tuple, got {type(operand).__name__}")
        if len(operand) == 0:
            return INVALID
        return operand[0]  # type: ignore


class LastOp[ResultT](Operation, UnaryMorphism[ResultT | Sentinel]):
    """Last element: seq[-1]. Returns Invalid if empty."""

    def _apply(self, operand: object) -> ResultT | Sentinel:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"last() requires list or tuple, got {type(operand).__name__}")
        if len(operand) == 0:
            return INVALID
        return operand[-1]  # type: ignore


class IndexOfOp[T](Operation, BinaryMorphism[int | Sentinel]):
    """Find index of value: seq.index(value). Returns Invalid if not found."""

    def _apply(self, left: object, right: object) -> int | Sentinel:
        # left = sequence, right = value to find
        if not isinstance(left, (list, tuple)):
            raise TypeError(f"index_() requires list or tuple, got {type(left).__name__}")
        try:
            return list(left).index(right)
        except ValueError:
            return INVALID


class CountOp(Operation, BinaryMorphism[int]):
    """Count occurrences: seq.count(value)."""

    def _apply(self, left: object, right: object) -> int | Sentinel:
        # left = sequence, right = value to count
        if not isinstance(left, (list, tuple)):
            raise TypeError(f"count_() requires list or tuple, got {type(left).__name__}")
        return list(left).count(right)


class FindOp[T](Operation, NAryMorphism[T | Sentinel]):
    """Find first element matching predicate. Returns Invalid if not found.

    Example:
        >>> FindOp(items, lambda x: x > 100)
    """

    def __init__(self, operand: object, fn: Callable[[T], bool]) -> None:
        """Initialize find operation.

        Args:
            operand: Term that produces a sequence
            fn: Predicate function
        """
        super().__init__(operand)
        self._fn = fn

    def _apply(self, operand: object) -> T | Sentinel:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"find() requires list or tuple, got {type(operand).__name__}")
        for item in operand:
            if self._fn(item):
                return item  # type: ignore
        return INVALID

    def __repr__(self) -> str:
        return f"FindOp({self._children[0]!r}, {self._fn!r})"


class FindIndexOp[T](Operation, NAryMorphism[int | Sentinel]):
    """Find index of first element matching predicate. Returns Invalid if not found.

    Example:
        >>> FindIndexOp(items, lambda x: x > 100)
    """

    def __init__(self, operand: object, fn: Callable[[T], bool]) -> None:
        """Initialize find index operation.

        Args:
            operand: Term that produces a sequence
            fn: Predicate function
        """
        super().__init__(operand)
        self._fn = fn

    def _apply(self, operand: object) -> int | Sentinel:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"find_index() requires list or tuple, got {type(operand).__name__}")
        for i, item in enumerate(operand):
            if self._fn(item):
                return i
        return INVALID

    def __repr__(self) -> str:
        return f"FindIndexOp({self._children[0]!r}, {self._fn!r})"


class JoinOp(Operation, BinaryMorphism[str | Sentinel]):
    """Join strings: sep.join(seq)."""

    def _apply(self, left: object, right: object) -> str | Sentinel:
        # left = sequence, right = separator
        if not isinstance(left, (list, tuple)):
            raise TypeError(f"join() requires list or tuple, got {type(left).__name__}")
        if not isinstance(right, str):
            raise TypeError(f"join() separator must be str, got {type(right).__name__}")
        try:
            return right.join(str(x) for x in left)
        except Exception:
            return INVALID
