"""Collection transformation operations.

MapOp: Map function over sequence (list(map(fn, seq)))
FilterOp: Filter by predicate (list(filter(fn, seq)))
ReduceOp: Reduce to single value (functools.reduce(fn, seq, initial))
SortedOp: Sorted list (sorted(seq, reverse=reverse))
ReversedOp: Reversed list (list(reversed(seq)))
"""

from __future__ import annotations

from functools import reduce as functools_reduce
from typing import TYPE_CHECKING

from everyshape.typing import NAN, Sentinel

from ..core import NAryOp, UnaryOp


if TYPE_CHECKING:
    from collections.abc import Callable

    from everyshape.term import Term
    from everyshape.types import UnionBaseType


__all__ = [
    "FilterOp",
    "MapOp",
    "ReduceOp",
    "ReversedOp",
    "SortedOp",
]


type OpArgument = Term | UnionBaseType


class SortedOp[ResultT](UnaryOp[list[ResultT] | Sentinel]):
    """Sorted list: sorted(seq, reverse=reverse)."""

    def __init__(self, operand: OpArgument, *, reverse: bool = False) -> None:
        """Initialize sorted operation.

        Args:
            operand: Sequence to sort
            reverse: If True, sort in descending order
        """
        super().__init__(operand)
        self._reverse = reverse

    def _apply_op(self, operand: object) -> list[ResultT] | Sentinel:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"sorted_() requires list or tuple, got {type(operand).__name__}")
        try:
            return sorted(operand, reverse=self._reverse)  # type: ignore
        except TypeError:
            return NAN

    def __repr__(self) -> str:
        return f"SortedOp({self.children[0]!r}, reverse={self._reverse})"


class ReversedOp[ResultT](UnaryOp[list[ResultT]]):
    """Reversed list: list(reversed(seq))."""

    def _apply_op(self, operand: object) -> list[ResultT]:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"reversed_() requires list or tuple, got {type(operand).__name__}")
        return list(reversed(operand))  # type: ignore


class MapOp[T, T2](NAryOp[list[T2]]):
    """Map function over sequence: list(map(fn, seq)).

    Example:
        >>> MapOp(prices, lambda x: x * 2)
        >>> MapOp(items, str)
    """

    def __init__(self, operand: OpArgument, fn: Callable[[T], T2]) -> None:
        """Initialize map operation.

        Args:
            operand: Term that produces a sequence
            fn: Function to apply to each element
        """
        super().__init__(operand)
        self._fn = fn

    def _apply_op(self, operand: object) -> list[T2]:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"map_() requires list or tuple, got {type(operand).__name__}")
        return list(map(self._fn, operand))

    def __repr__(self) -> str:
        return f"MapOp({self.children[0]!r}, {self._fn!r})"


class FilterOp[T](NAryOp[list[T]]):
    """Filter sequence by predicate: list(filter(fn, seq)).

    Example:
        >>> FilterOp(prices, lambda x: x > 100)
        >>> FilterOp(items, bool)  # remove falsy values
    """

    def __init__(self, operand: OpArgument, fn: Callable[[T], bool]) -> None:
        """Initialize filter operation.

        Args:
            operand: Term that produces a sequence
            fn: Predicate function - keep element if returns truthy
        """
        super().__init__(operand)
        self._fn = fn

    def _apply_op(self, operand: object) -> list[T]:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"filter_() requires list or tuple, got {type(operand).__name__}")
        return list(filter(self._fn, operand))  # type: ignore

    def __repr__(self) -> str:
        return f"FilterOp({self.children[0]!r}, {self._fn!r})"


class ReduceOp[T, T2](NAryOp[T2 | Sentinel]):
    """Reduce sequence to single value: functools.reduce(fn, seq, initial).

    Example:
        >>> ReduceOp(prices, lambda acc, x: acc + x, 0)
        >>> ReduceOp(items, lambda acc, x: acc * x, 1)
    """

    def __init__(self, operand: OpArgument, fn: Callable[[T2, T], T2], initial: T2) -> None:
        """Initialize reduce operation.

        Args:
            operand: Term that produces a sequence
            fn: Reducer function (accumulator, element) -> new_accumulator
            initial: Initial accumulator value
        """
        super().__init__(operand)
        self._fn = fn
        self._initial = initial

    def _apply_op(self, operand: object) -> T2 | Sentinel:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"reduce_() requires list or tuple, got {type(operand).__name__}")
        try:
            return functools_reduce(self._fn, operand, self._initial)
        except Exception:
            return NAN

    def __repr__(self) -> str:
        return f"ReduceOp({self.children[0]!r}, {self._fn!r}, {self._initial!r})"
