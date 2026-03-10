"""Iterable transformation morphisms.

MapOp: Map function over sequence (list(map(fn, seq)))
FilterOp: Filter by predicate (list(filter(fn, seq)))
SortedOp: Sorted list (sorted(seq, reverse=reverse))
ReversedOp: Reversed list (list(reversed(seq)))
PluckOp: Extract field from each element ([x[key] for x in seq])
ToDictOp: Build dict from sequence ({key_fn(x): val_fn(x) for x in seq})
FilterByOp: Filter by field value ([x for x in seq if x[key] == value])
FlattenOp: Flatten one level ([item for sub in seq for item in sub])
UniqueOp: Unique elements preserving order (list(dict.fromkeys(seq)))
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING

from everybase.core import INVALID, BinaryOperation, Sentinel, TernaryOperation, UnaryOperation


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
    """Sorted list: sorted(seq, reverse=reverse)."""

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


class ReversedOp[ResultT](UnaryOperation[list[ResultT]]):
    """Reversed list: list(reversed(seq))."""

    def apply(self, operand: object) -> list[ResultT]:
        """Apply."""
        if not isinstance(operand, Sequence):
            raise TypeError(f"reversed_() requires sequence, got {type(operand).__name__}")
        return list(reversed(operand))  # type: ignore


class MapOp[T, T2](UnaryOperation[list[T2]]):
    """Map function over sequence: list(map(fn, seq)).

    Example:
        >>> MapOp(prices, lambda x: x * 2)
        >>> MapOp(items, str)
    """

    def __init__(self, operand: object, fn: Callable[[T], T2]) -> None:
        """Initialize map operation.

        Args:
            operand: Term that produces a sequence
            fn: Function to apply to each element
        """
        super().__init__(operand)
        self._fn = fn

    def apply(self, operand: object) -> list[T2]:
        """Apply."""
        if not isinstance(operand, Iterable):
            raise TypeError(f"map_() requires iterable, got {type(operand).__name__}")
        return list(map(self._fn, operand))

    def __repr__(self) -> str:
        return f"MapOp({self._children[0]!r}, {self._fn!r})"


class FilterOp[T](UnaryOperation[list[T]]):
    """Filter sequence by predicate: list(filter(fn, seq)).

    Example:
        >>> FilterOp(prices, lambda x: x > 100)
        >>> FilterOp(items, bool)  # remove falsy values
    """

    def __init__(self, operand: object, fn: Callable[[T], bool]) -> None:
        """Initialize filter operation.

        Args:
            operand: Term that produces a sequence
            fn: Predicate function - keep element if returns truthy
        """
        super().__init__(operand)
        self._fn = fn

    def apply(self, operand: object) -> list[T]:
        """Apply."""
        if not isinstance(operand, Iterable):
            raise TypeError(f"filter_() requires iterable, got {type(operand).__name__}")
        return list(filter(self._fn, operand))  # type: ignore

    def __repr__(self) -> str:
        return f"FilterOp({self._children[0]!r}, {self._fn!r})"


class PluckOp[T](BinaryOperation[list[T]]):
    """Extract field from each element: [x[key] for x in seq].

    Both operand and key are resolved as terms at execution time.

    Example:
        >>> PluckOp(token_balances, "mint")
    """

    def apply(self, left: object, right: object) -> list[T] | Sentinel:
        """Apply."""
        if not isinstance(left, Iterable):
            raise TypeError(f"pluck_() requires iterable, got {type(left).__name__}")
        try:
            return [item[right] for item in left]  # type: ignore
        except (KeyError, TypeError):
            return INVALID


class ToDictOp[K, V](UnaryOperation[dict[K, V]]):
    """Build dict from sequence: {key_fn(x): val_fn(x) for x in seq}.

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
            operand: Term that produces a sequence
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


class FilterByOp[T](TernaryOperation[list[T]]):
    """Filter by field value: [x for x in seq if x[key] == value].

    All three operands (collection, field, value) are resolved as terms
    at execution time — so both field name and value can be dynamic.

    Example:
        >>> FilterByOp(balances, "mint", t.current_mint)
    """

    def apply(self, first: object, second: object, third: object) -> list[T] | Sentinel:
        """Apply: first=collection, second=field, third=value."""
        if not isinstance(first, Iterable):
            raise TypeError(f"filter_by_() requires iterable, got {type(first).__name__}")
        try:
            return [item for item in first if item[second] == third]  # type: ignore
        except (KeyError, TypeError):
            return INVALID


class FlattenOp(UnaryOperation[list]):
    """Flatten one level: [item for sub in iterable for item in sub]."""

    def apply(self, operand: object) -> list | Sentinel:
        """Apply."""
        if not isinstance(operand, Iterable):
            raise TypeError(f"Flatten requires iterable, got {type(operand).__name__}")
        try:
            return [item for sub in operand for item in sub]  # type: ignore
        except TypeError:
            return INVALID


class UniqueOp(UnaryOperation[list]):
    """Unique elements preserving order: list(dict.fromkeys(iterable))."""

    def __init__(self, operand: object, key_fn: Callable | None = None) -> None:
        """Initialize."""
        super().__init__(operand)
        self._key_fn = key_fn

    def apply(self, operand: object) -> list | Sentinel:
        """Apply."""
        if not isinstance(operand, Iterable):
            raise TypeError(f"Unique requires iterable, got {type(operand).__name__}")
        try:
            if self._key_fn is None:
                return list(dict.fromkeys(operand))
            seen: set = set()
            result: list = []
            for item in operand:
                k = self._key_fn(item)
                if k not in seen:
                    seen.add(k)
                    result.append(item)
            return result
        except Exception:
            return INVALID

    def __repr__(self) -> str:
        if self._key_fn is not None:
            return f"UniqueOp({self._children[0]!r}, key={self._key_fn!r})"
        return f"UniqueOp({self._children[0]!r})"
