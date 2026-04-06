"""Iterable transformations — Value-returning factories over op Ops.

Reversed, Flatten, Unique, Pluck, FilterBy (lazy -> IteratorI)
Sorted (eager -> ListI)
"""

from __future__ import annotations

from nu.collections import IteratorI, ListI
from nu.ops import FilterByOp, FlattenOp, PluckOp, ReversedOp, SortedOp, UniqueOp


__all__ = [
    "FilterBy",
    "Flatten",
    "Pluck",
    "Reversed",
    "Sorted",
    "Unique",
]


def Reversed(iterable: object) -> IteratorI:  # noqa: N802
    """Reversed sequence. Lazy."""
    return IteratorI(ReversedOp(iterable))


def Flatten(iterable: object) -> IteratorI:  # noqa: N802
    """Flatten one level of nesting. Lazy."""
    return IteratorI(FlattenOp(iterable))


def Unique(iterable: object) -> IteratorI:  # noqa: N802
    """Unique elements preserving order. Lazy."""
    return IteratorI(UniqueOp(iterable))


def Pluck(iterable: object, field: object) -> IteratorI:  # noqa: N802
    """Extract field from each element. Lazy."""
    return IteratorI(PluckOp(iterable, field))


def FilterBy(iterable: object, field: object, value: object) -> IteratorI:  # noqa: N802
    """Filter elements where field equals value. Lazy."""
    return IteratorI(FilterByOp(iterable, field, value))


def Sorted(iterable: object, *, reverse: object = False) -> ListI:  # noqa: N802
    """Sorted iterable. Terminal — inherently eager."""
    return ListI(SortedOp(iterable, reverse))
