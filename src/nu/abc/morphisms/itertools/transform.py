"""Iterable transformation morphisms — lazy iterators.

Transform morphisms return lazy iterators instead of materialized lists.
Use ToList/ToSet/ToDict to explicitly materialize.

MapOp: map(fn, seq) -> Iterator
FilterOp: filter(fn, seq) -> Iterator
SortedOp: sorted(seq) -> list (terminal — inherently eager)
ReversedOp: reversed(seq) -> Iterator
PluckOp: (x[key] for x in seq) -> Iterator
ToDictOp: {key_fn(x): val_fn(x) for x in seq} -> dict (terminal)
FilterByOp: (x for x in seq if x[key] == value) -> Iterator
FlattenOp: chain.from_iterable(seq) -> Iterator
UniqueOp: unique elements preserving order -> Iterator
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from itertools import chain as itertools_chain
from typing import TYPE_CHECKING

from nu.core import INVALID, BinaryOperation, Sentinel, TernaryOperation, UnaryOperation


if TYPE_CHECKING:
    from collections.abc import Callable


__all__ = [
    "FilterByOp",
    "FilterOp",
    "FlattenOp",
    "MapOp",
    "PluckOp",
    "ReversedOp",
    "SortedOp",
    "ToDictOp",
    "UniqueOp",
]


class SortedOp[ResultT](BinaryOperation[list[ResultT]]):
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


class ReversedOp[ResultT](UnaryOperation[Iterator[ResultT]]):
    """Reversed sequence: reversed(seq) -> lazy iterator."""

    def apply(self, operand: object) -> Iterator[ResultT]:
        """Apply."""
        if not isinstance(operand, Sequence):
            raise TypeError(f"reversed_() requires sequence, got {type(operand).__name__}")
        return reversed(operand)  # type: ignore


class MapOp[T, T2](UnaryOperation[Iterator[T2]]):
    """Map function over iterable: map(fn, seq) -> lazy iterator.

    Example:
        >>> MapOp(prices, lambda x: x * 2)
        >>> MapOp(items, str)
    """

    def __init__(self, operand: object, fn: Callable[[T], T2]) -> None:
        """Initialize map operation.

        Args:
            operand: Term that produces an iterable
            fn: Function to apply to each element
        """
        super().__init__(operand)
        self._fn = fn

    def apply(self, operand: object) -> Iterator[T2]:
        """Apply."""
        if not isinstance(operand, Iterable):
            raise TypeError(f"map_() requires iterable, got {type(operand).__name__}")
        return map(self._fn, operand)

    def __repr__(self) -> str:
        return f"MapOp({self._children[0]!r}, {self._fn!r})"


class FilterOp[T](UnaryOperation[Iterator[T]]):
    """Filter iterable by predicate: filter(fn, seq) -> lazy iterator.

    Example:
        >>> FilterOp(prices, lambda x: x > 100)
        >>> FilterOp(items, bool)  # remove falsy values
    """

    def __init__(self, operand: object, fn: Callable[[T], bool]) -> None:
        """Initialize filter operation.

        Args:
            operand: Term that produces an iterable
            fn: Predicate function - keep element if returns truthy
        """
        super().__init__(operand)
        self._fn = fn

    def apply(self, operand: object) -> Iterator[T]:
        """Apply."""
        if not isinstance(operand, Iterable):
            raise TypeError(f"filter_() requires iterable, got {type(operand).__name__}")
        return filter(self._fn, operand)  # type: ignore

    def __repr__(self) -> str:
        return f"FilterOp({self._children[0]!r}, {self._fn!r})"


class PluckOp[T](BinaryOperation[Iterator[T]]):
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


class ToDictOp[K, V](UnaryOperation[dict[K, V]]):
    """Build dict from iterable: {key_fn(x): val_fn(x) for x in seq}. Terminal.

    Example:
        >>> ToDictOp(balances, lambda b: b["owner"], lambda b: int(b["amount"]))
    """

    def __init__(
        self,
        operand: object,
        key_fn: Callable[[object], K],
        val_fn: Callable[[object], V],
    ) -> None:
        """Initialize.

        Args:
            operand: Term that produces an iterable
            key_fn: Function to extract dict key from each element
            val_fn: Function to extract dict value from each element
        """
        super().__init__(operand)
        self._key_fn = key_fn
        self._val_fn = val_fn

    def apply(self, operand: object) -> dict[K, V] | Sentinel:
        """Apply."""
        if not isinstance(operand, Iterable):
            raise TypeError(f"to_dict_() requires iterable, got {type(operand).__name__}")
        try:
            return {self._key_fn(item): self._val_fn(item) for item in operand}
        except Exception:
            return INVALID

    def __repr__(self) -> str:
        return f"ToDictOp({self._children[0]!r}, {self._key_fn!r}, {self._val_fn!r})"


class FilterByOp[T](TernaryOperation[Iterator[T]]):
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


class FlattenOp(UnaryOperation[Iterator]):
    """Flatten one level: chain.from_iterable(seq) -> lazy iterator."""

    def apply(self, operand: object) -> Iterator | Sentinel:
        """Apply."""
        if not isinstance(operand, Iterable):
            raise TypeError(f"Flatten requires iterable, got {type(operand).__name__}")
        try:
            return itertools_chain.from_iterable(operand)  # type: ignore
        except TypeError:
            return INVALID


class UniqueOp(UnaryOperation[Iterator]):
    """Unique elements preserving order -> lazy iterator."""

    def __init__(self, operand: object, key_fn: Callable | None = None) -> None:
        """Initialize."""
        super().__init__(operand)
        self._key_fn = key_fn

    def apply(self, operand: object) -> Iterator | Sentinel:
        """Apply."""
        if not isinstance(operand, Iterable):
            raise TypeError(f"Unique requires iterable, got {type(operand).__name__}")

        key_fn = self._key_fn

        def _gen() -> Iterator:
            seen: set = set()
            for item in operand:
                k = key_fn(item) if key_fn is not None else item
                if k not in seen:
                    seen.add(k)
                    yield item

        try:
            return _gen()
        except Exception:
            return INVALID

    def __repr__(self) -> str:
        if self._key_fn is not None:
            return f"UniqueOp({self._children[0]!r}, key={self._key_fn!r})"
        return f"UniqueOp({self._children[0]!r})"
