"""Iterable transformation ops — lazy iterators.

Transform ops return lazy iterators instead of materialized lists.
Use ToList/ToSet/ToDict to explicitly materialize.

SortedOp: sorted(seq) -> list (terminal — inherently eager)
ReversedOp: reversed(seq) -> Iterator
PluckOp: (x[key] for x in seq) -> Iterator
FilterByOp: (x for x in seq if x[key] == value) -> Iterator
FlattenOp: chain.from_iterable(seq) -> Iterator
UniqueOp: unique elements preserving order -> Iterator
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from itertools import chain as itertools_chain

from nu.terms import INVALID, BinaryCalc, Sentinel, TernaryCalc, UnaryCalc


__all__ = [
    "FilterByOp",
    "FlattenOp",
    "PluckOp",
    "ReversedOp",
    "SortedOp",
    "UniqueOp",
]


class SortedOp[ResultT](BinaryCalc[list[ResultT]]):
    """Sorted list: sorted(seq, reverse=reverse). Terminal — inherently eager."""

    def apply(self, left: object, right: object) -> list[ResultT] | Sentinel:
        """Apply."""
        if not isinstance(left, Iterable):
            raise TypeError(f"sorted_() requires iterable, got {type(left).__name__}")
        try:
            return sorted(left, reverse=right)  # type: ignore
        except TypeError:
            return INVALID

    def __repr__(self) -> str:
        return f"SortedOp({self._children[0]!r}, reverse={self._children[1]!r})"


class ReversedOp[ResultT](UnaryCalc[Iterator[ResultT]]):
    """Reversed sequence: reversed(seq) -> lazy iterator."""

    def apply(self, operand: object) -> Iterator[ResultT]:
        """Apply."""
        if not isinstance(operand, Sequence):
            raise TypeError(f"reversed_() requires sequence, got {type(operand).__name__}")
        return reversed(operand)  # type: ignore


class PluckOp[T](BinaryCalc[Iterator[T]]):
    """Extract field from each element: (x[key] for x in seq) -> lazy iterator.

    Both operand and key are resolved as terms at execution time.

    Example:
        >>> PluckOp(token_balances, "mint")
    """

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


class FilterByOp[T](TernaryCalc[Iterator[T]]):
    """Filter by field value: (x for x in seq if x[key] == value) -> lazy iterator.

    All three operands (collection, field, value) are resolved as terms
    at execution time — so both field name and value can be dynamic.

    Example:
        >>> FilterByOp(balances, "mint", t.current_mint)
    """

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


class FlattenOp(UnaryCalc[Iterator]):
    """Flatten one level: chain.from_iterable(seq) -> lazy iterator."""

    def apply(self, operand: object) -> Iterator | Sentinel:
        """Apply."""
        if not isinstance(operand, Iterable):
            raise TypeError(f"Flatten requires iterable, got {type(operand).__name__}")
        try:
            return itertools_chain.from_iterable(operand)  # type: ignore
        except TypeError:
            return INVALID


class UniqueOp(UnaryCalc[Iterator]):
    """Unique elements preserving order -> lazy iterator."""

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
