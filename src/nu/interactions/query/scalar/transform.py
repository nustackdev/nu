"""Iterable transformation ops — lazy iterators.

Transform ops return lazy iterators instead of materialized lists.
Use ToList/ToSet/ToDict to explicitly materialize.

Sorted: sorted(seq) -> list (terminal — inherently eager)
Reversed: reversed(seq) -> Iterator
Pluck: (x[key] for x in seq) -> Iterator
FilterBy: (x for x in seq if x[key] == value) -> Iterator
Flatten: chain.from_iterable(seq) -> Iterator
Unique: unique elements preserving order -> Iterator
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from itertools import chain as itertools_chain
from typing import ClassVar

from nu.terms import INVALID, BinaryQuery, Mode, Sentinel, TernaryQuery, UnaryQuery


__all__ = [
    "FilterBy",
    "Flatten",
    "Pluck",
    "Reversed",
    "Sorted",
    "Unique",
]


class Sorted[ResultT](BinaryQuery[list[ResultT]]):
    """Sorted list: sorted(seq, reverse=reverse). Terminal — inherently eager."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> list[ResultT] | Sentinel:
        """Apply."""
        if not isinstance(left, Iterable):
            raise TypeError(f"sorted_() requires iterable, got {type(left).__name__}")
        try:
            return sorted(left, reverse=right)  # type: ignore
        except TypeError:
            return INVALID

    def __repr__(self) -> str:
        return f"Sorted({self._children[0]!r}, reverse={self._children[1]!r})"


class Reversed[ResultT](UnaryQuery[Iterator[ResultT]]):
    """Reversed sequence: reversed(seq) -> lazy iterator."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> Iterator[ResultT]:
        """Apply."""
        if not isinstance(operand, Sequence):
            raise TypeError(f"reversed_() requires sequence, got {type(operand).__name__}")
        return reversed(operand)  # type: ignore


class Pluck[T](BinaryQuery[Iterator[T]]):
    """Extract field from each element: (x[key] for x in seq) -> lazy iterator.

    Both operand and key are resolved as terms at execution time.

    Example:
        >>> Pluck(token_balances, "mint")
    """

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> Iterator[T] | Sentinel:
        """Apply."""
        if not isinstance(left, Iterable):
            raise TypeError(f"pluck_() requires iterable, got {type(left).__name__}")

        def _gen() -> Iterator[T]:
            for item in left:
                yield item[right]  # type: ignore

        try:
            return _gen()
        except (KeyError, TypeError):
            return INVALID


class FilterBy[T](TernaryQuery[Iterator[T]]):
    """Filter by field value: (x for x in seq if x[key] == value) -> lazy iterator.

    All three operands (collection, field, value) are resolved as terms
    at execution time — so both field name and value can be dynamic.

    Example:
        >>> FilterBy(balances, "mint", t.current_mint)
    """

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, first: object, second: object, third: object) -> Iterator[T] | Sentinel:
        """Apply: first=collection, second=field, third=value."""
        if not isinstance(first, Iterable):
            raise TypeError(f"filter_by_() requires iterable, got {type(first).__name__}")

        def _gen() -> Iterator[T]:
            for item in first:
                if item[second] == third:  # type: ignore
                    yield item  # type: ignore

        try:
            return _gen()
        except (KeyError, TypeError):
            return INVALID


class Flatten(UnaryQuery[Iterator]):
    """Flatten one level: chain.from_iterable(seq) -> lazy iterator."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> Iterator | Sentinel:
        """Apply."""
        if not isinstance(operand, Iterable):
            raise TypeError(f"Flatten requires iterable, got {type(operand).__name__}")
        try:
            return itertools_chain.from_iterable(operand)  # type: ignore
        except TypeError:
            return INVALID


class Unique(UnaryQuery[Iterator]):
    """Unique elements preserving order -> lazy iterator."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> Iterator | Sentinel:
        """Apply."""
        if not isinstance(operand, Iterable):
            raise TypeError(f"Unique requires iterable, got {type(operand).__name__}")

        def _gen() -> Iterator:
            seen: set = set()
            for item in operand:
                if item not in seen:
                    seen.add(item)
                    yield item

        try:
            return _gen()
        except Exception:
            return INVALID
