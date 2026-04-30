"""Iterable reduction ops - terminal operations that consume iterables."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, ClassVar

from nu.terms.query import ScalarQuery
from nu.terms.sentinels import INVALID
from nu.terms.types import Mode


__all__ = [
    "AllElem",
    "AnyElem",
    "MaxElem",
    "MinElem",
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
            msg = f"Sum() requires iterable, got {type(operand).__name__}"
            raise TypeError(msg)
        try:
            return sum(operand)
        except TypeError:
            return INVALID


class MinElem(ScalarQuery):
    """Minimum element."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:
        operand = ops[0]
        if not isinstance(operand, Iterable):
            msg = f"MinElem() requires iterable, got {type(operand).__name__}"
            raise TypeError(msg)
        try:
            return min(operand)
        except (TypeError, ValueError):
            return INVALID


class MaxElem(ScalarQuery):
    """Maximum element."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:
        operand = ops[0]
        if not isinstance(operand, Iterable):
            msg = f"MaxElem() requires iterable, got {type(operand).__name__}"
            raise TypeError(msg)
        try:
            return max(operand)
        except (TypeError, ValueError):
            return INVALID


class AnyElem(ScalarQuery):
    """Any truthy element."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: object) -> None:
        super().__init__(operand)

    def _apply(self, ctx: object, ops: list[object]) -> bool:
        operand = ops[0]
        if not isinstance(operand, Iterable):
            msg = f"AnyElem() requires iterable, got {type(operand).__name__}"
            raise TypeError(msg)
        return any(operand)


class AllElem(ScalarQuery):
    """All truthy elements."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: object) -> None:
        super().__init__(operand)

    def _apply(self, ctx: object, ops: list[object]) -> bool:
        operand = ops[0]
        if not isinstance(operand, Iterable):
            msg = f"AllElem() requires iterable, got {type(operand).__name__}"
            raise TypeError(msg)
        return all(operand)
