"""Higher-order search morphisms.

FindOp: Find first element matching predicate
FindIndexOp: Find index of first element matching predicate
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from nu.terms import INVALID, Sentinel, UnaryOperation


if TYPE_CHECKING:
    from collections.abc import Callable


__all__ = [
    "FindIndexOp",
    "FindOp",
]


class FindOp[T](UnaryOperation[T]):
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

    def apply(self, operand: object) -> T | Sentinel:
        """Apply."""
        if not isinstance(operand, Iterable):
            raise TypeError(f"find() requires iterable, got {type(operand).__name__}")
        for item in operand:
            if self._fn(item):
                return item  # type: ignore
        return INVALID

    def __repr__(self) -> str:
        return f"FindOp({self._children[0]!r}, {self._fn!r})"


class FindIndexOp[T](UnaryOperation[int]):
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

    def apply(self, operand: object) -> int | Sentinel:
        """Apply."""
        if not isinstance(operand, Iterable):
            raise TypeError(f"find_index() requires iterable, got {type(operand).__name__}")
        for i, item in enumerate(operand):
            if self._fn(item):
                return i
        return INVALID

    def __repr__(self) -> str:
        return f"FindIndexOp({self._children[0]!r}, {self._fn!r})"
