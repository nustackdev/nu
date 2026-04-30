"""Iterable transformation ops - lazy iterators."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from itertools import chain as itertools_chain
from typing import Any, ClassVar

from nu.terms.query import ScalarQuery
from nu.terms.sentinels import INVALID
from nu.terms.types import Mode


__all__ = [
    "FilterBy",
    "Flatten",
    "Pluck",
    "Reversed",
    "Sorted",
    "Unique",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class Sorted(ScalarQuery):
    """Sorted list: sorted(seq, reverse=reverse)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, iterable: Any, reverse: Any = False) -> None:  # noqa: ANN401
        super().__init__(iterable, reverse)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        left, right = ops
        if not isinstance(left, Iterable):
            msg = f"sorted_() requires iterable, got {type(left).__name__}"
            raise TypeError(msg)
        try:
            return sorted(left, reverse=bool(right))
        except TypeError:
            return INVALID


class Reversed(ScalarQuery):
    """Reversed sequence: reversed(seq) -> lazy iterator."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Iterator:  # noqa: ANN401
        operand = ops[0]
        if not isinstance(operand, Sequence):
            msg = f"reversed_() requires sequence, got {type(operand).__name__}"
            raise TypeError(msg)
        return reversed(operand)


class Pluck(ScalarQuery):
    """Extract field from each element."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, iterable: Any, key: Any) -> None:  # noqa: ANN401
        super().__init__(iterable, key)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        left, right = ops
        if not isinstance(left, Iterable):
            msg = f"pluck_() requires iterable, got {type(left).__name__}"
            raise TypeError(msg)

        def _gen() -> Iterator:
            for item in left:
                yield item[right]

        return _gen()


class FilterBy(ScalarQuery):
    """Filter by field value."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, iterable: Any, field: Any, value: Any) -> None:  # noqa: ANN401
        super().__init__(iterable, field, value)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        first, second, third = ops
        if not isinstance(first, Iterable):
            msg = f"filter_by_() requires iterable, got {type(first).__name__}"
            raise TypeError(msg)

        def _gen() -> Iterator:
            for item in first:
                if item[second] == third:
                    yield item

        return _gen()


class Flatten(ScalarQuery):
    """Flatten one level."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        operand = ops[0]
        if not isinstance(operand, Iterable):
            msg = f"Flatten requires iterable, got {type(operand).__name__}"
            raise TypeError(msg)
        try:
            return itertools_chain.from_iterable(operand)
        except TypeError:
            return INVALID


class Unique(ScalarQuery):
    """Unique elements preserving order."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        operand = ops[0]
        if not isinstance(operand, Iterable):
            msg = f"Unique requires iterable, got {type(operand).__name__}"
            raise TypeError(msg)

        def _gen() -> Iterator:
            seen: set = set()
            for item in operand:
                if item not in seen:
                    seen.add(item)
                    yield item

        return _gen()
