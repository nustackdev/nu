"""Collection search operations.

FirstOp: First element (seq[0])
LastOp: Last element (seq[-1])
IndexOfOp: Find index of value (seq.index(value))
FindOp: Find first element matching predicate
FindIndexOp: Find index of first element matching predicate
CountOp: Count occurrences (seq.count(value))
JoinOp: Join strings (sep.join(seq))
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from everyshape.typing import NAN, Sentinel

from ..base import BinaryOp, NAryOp, UnaryOp


if TYPE_CHECKING:
    from collections.abc import Callable

    from ...context import Context
    from ...term import Term
    from ...type import UnionBaseType


__all__ = [
    "CountOp",
    "FindIndexOp",
    "FindOp",
    "FirstOp",
    "IndexOfOp",
    "JoinOp",
    "LastOp",
]


type OpArgument = Term | UnionBaseType


class FirstOp[ResultT](UnaryOp[ResultT | Sentinel]):
    """First element: seq[0]. Returns NaN if empty."""

    def _apply_op(self, operand: object) -> ResultT | Sentinel:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"first() requires list or tuple, got {type(operand).__name__}")
        if len(operand) == 0:
            return NAN
        return operand[0]  # type: ignore


class LastOp[ResultT](UnaryOp[ResultT | Sentinel]):
    """Last element: seq[-1]. Returns NaN if empty."""

    def _apply_op(self, operand: object) -> ResultT | Sentinel:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"last() requires list or tuple, got {type(operand).__name__}")
        if len(operand) == 0:
            return NAN
        return operand[-1]  # type: ignore


class IndexOfOp[T](BinaryOp[int | Sentinel]):
    """Find index of value: seq.index(value). Returns NaN if not found."""

    def _apply_op(self, left: object, right: object) -> int | Sentinel:
        # left = sequence, right = value to find
        if not isinstance(left, (list, tuple)):
            raise TypeError(f"index_() requires list or tuple, got {type(left).__name__}")
        try:
            return list(left).index(right)
        except ValueError:
            return NAN


class CountOp(BinaryOp[int]):
    """Count occurrences: seq.count(value)."""

    def _apply_op(self, left: object, right: object) -> int | Sentinel:
        # left = sequence, right = value to count
        if not isinstance(left, (list, tuple)):
            raise TypeError(f"count_() requires list or tuple, got {type(left).__name__}")
        return list(left).count(right)


class FindOp[T](NAryOp[T | Sentinel]):
    """Find first element matching predicate. Returns NaN if not found.

    Example:
        >>> FindOp(items, lambda x: x > 100)
    """

    def __init__(self, operand: OpArgument, fn: Callable[[T], bool]) -> None:
        """Initialize find operation.

        Args:
            operand: Term that produces a sequence
            fn: Predicate function
        """
        self.children = (cast("Term", operand),)
        self._fn = fn

    def execute(self, context: Context) -> T | Sentinel:
        """Execute find operation."""
        operand_val = self.children[0].execute(context)
        if not isinstance(operand_val, (list, tuple)):
            raise TypeError(f"find() requires list or tuple, got {type(operand_val).__name__}")
        for item in operand_val:
            if self._fn(item):
                return item  # type: ignore
        return NAN

    def __repr__(self) -> str:
        return f"FindOp({self.children[0]!r}, {self._fn!r})"


class FindIndexOp[T](NAryOp[int | Sentinel]):
    """Find index of first element matching predicate. Returns NaN if not found.

    Example:
        >>> FindIndexOp(items, lambda x: x > 100)
    """

    def __init__(self, operand: OpArgument, fn: Callable[[T], bool]) -> None:
        """Initialize find index operation.

        Args:
            operand: Term that produces a sequence
            fn: Predicate function
        """
        self.children = (cast("Term", operand),)
        self._fn = fn

    def execute(self, context: Context) -> int | Sentinel:
        """Execute find index operation."""
        operand_val = self.children[0].execute(context)
        if not isinstance(operand_val, (list, tuple)):
            raise TypeError(
                f"find_index() requires list or tuple, got {type(operand_val).__name__}"
            )
        for i, item in enumerate(operand_val):
            if self._fn(item):
                return i
        return NAN

    def __repr__(self) -> str:
        return f"FindIndexOp({self.children[0]!r}, {self._fn!r})"


class JoinOp(BinaryOp[str | Sentinel]):
    """Join strings: sep.join(seq)."""

    def _apply_op(self, left: object, right: object) -> str | Sentinel:
        # left = sequence, right = separator
        if not isinstance(left, (list, tuple)):
            raise TypeError(f"join() requires list or tuple, got {type(left).__name__}")
        if not isinstance(right, str):
            raise TypeError(f"join() separator must be str, got {type(right).__name__}")
        try:
            return right.join(str(x) for x in left)
        except Exception:
            return NAN
