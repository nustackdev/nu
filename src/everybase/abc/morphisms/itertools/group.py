"""Iterable grouping morphisms — GroupBy, Partition."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from everybase.core import INVALID, Sentinel, UnaryOperation


if TYPE_CHECKING:
    from collections.abc import Callable


__all__ = [
    "GroupByOp",
    "PartitionOp",
]


class GroupByOp[K](UnaryOperation[list[tuple[K, list]]]):
    """Group by key function: [(k, [items]) for k in unique keys].

    Groups elements by key function. Elements with same key are grouped together
    regardless of input order (unlike itertools.groupby which requires sorted input).
    """

    def __init__(self, operand: object, key_fn: Callable[[object], K]) -> None:
        """Initialize."""
        super().__init__(operand)
        self._key_fn = key_fn

    def apply(self, operand: object) -> list[tuple[K, list]] | Sentinel:
        """Apply."""
        if not isinstance(operand, Iterable):
            raise TypeError(f"GroupBy requires iterable, got {type(operand).__name__}")
        try:
            groups: dict[K, list] = {}
            for item in operand:
                k = self._key_fn(item)
                groups.setdefault(k, []).append(item)
            return list(groups.items())
        except Exception:
            return INVALID

    def __repr__(self) -> str:
        return f"GroupByOp({self._children[0]!r}, {self._key_fn!r})"


class PartitionOp(UnaryOperation[tuple[list, list]]):
    """Partition by predicate: (matches, non_matches)."""

    def __init__(self, operand: object, predicate: Callable[[object], bool]) -> None:
        """Initialize."""
        super().__init__(operand)
        self._predicate = predicate

    def apply(self, operand: object) -> tuple[list, list] | Sentinel:
        """Apply."""
        if not isinstance(operand, Iterable):
            raise TypeError(f"Partition requires iterable, got {type(operand).__name__}")
        try:
            matches: list = []
            non_matches: list = []
            for item in operand:
                if self._predicate(item):
                    matches.append(item)
                else:
                    non_matches.append(item)
            return (matches, non_matches)
        except Exception:
            return INVALID

    def __repr__(self) -> str:
        return f"PartitionOp({self._children[0]!r}, {self._predicate!r})"
