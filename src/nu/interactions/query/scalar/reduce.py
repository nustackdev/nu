"""Iterable reduction ops - terminal operations that consume iterables."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, ClassVar

from nu.terms.query import ScalarQuery
from nu.terms.sentinels import INVALID
from nu.terms.types import Mode


__all__ = [
    "All",
    "Any",
    "Max",
    "Min",
    "Sum",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class Sum(ScalarQuery):
    """Sum of sequence elements."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:
        operand = ops[0]
        if not isinstance(operand, Iterable):
            msg = f"sum_() requires iterable, got {type(operand).__name__}"
            raise TypeError(msg)
        try:
            return sum(operand)
        except TypeError:
            return INVALID


class Min(ScalarQuery):
    """Minimum element."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:
        operand = ops[0]
        if not isinstance(operand, Iterable):
            msg = f"min_() requires iterable, got {type(operand).__name__}"
            raise TypeError(msg)
        try:
            return min(operand)
        except (TypeError, ValueError):
            return INVALID


class Max(ScalarQuery):
    """Maximum element."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:
        operand = ops[0]
        if not isinstance(operand, Iterable):
            msg = f"max_() requires iterable, got {type(operand).__name__}"
            raise TypeError(msg)
        try:
            return max(operand)
        except (TypeError, ValueError):
            return INVALID


class Any(ScalarQuery):
    """Any truthy element."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: object) -> None:
        super().__init__(operand)

    def _apply(self, ctx: object, ops: list[object]) -> bool:
        operand = ops[0]
        if not isinstance(operand, Iterable):
            msg = f"any_() requires iterable, got {type(operand).__name__}"
            raise TypeError(msg)
        return any(operand)


class All(ScalarQuery):
    """All truthy elements."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: object) -> None:
        super().__init__(operand)

    def _apply(self, ctx: object, ops: list[object]) -> bool:
        operand = ops[0]
        if not isinstance(operand, Iterable):
            msg = f"all_() requires iterable, got {type(operand).__name__}"
            raise TypeError(msg)
        return all(operand)
