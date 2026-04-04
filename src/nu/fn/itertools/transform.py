"""Iterable transformations — Value-returning factories over op Ops.

Map, Filter, Reversed, Flatten, Unique, Pluck, FilterBy (lazy -> IteratorI)
Sorted (eager -> ListI)
ToDict (eager -> DictI)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.ops.itertools.transform import (
    FilterByOp,
    FilterOp,
    FlattenOp,
    MapOp,
    PluckOp,
    ReversedOp,
    SortedOp,
    ToDictOp,
    UniqueOp,
)
from nu.interfaces import DictI, IteratorI, ListI


if TYPE_CHECKING:
    from collections.abc import Callable


__all__ = [
    "Filter",
    "FilterBy",
    "Flatten",
    "Map",
    "Pluck",
    "Reversed",
    "Sorted",
    "ToDict",
    "Unique",
]


def Map(iterable: object, fn: Callable) -> IteratorI:  # noqa: N802
    """Map function over iterable elements. Lazy."""
    return IteratorI(MapOp(iterable, fn))


def Filter(iterable: object, predicate: Callable) -> IteratorI:  # noqa: N802
    """Filter iterable by predicate. Lazy."""
    return IteratorI(FilterOp(iterable, predicate))


def Reversed(iterable: object) -> IteratorI:  # noqa: N802
    """Reversed sequence. Lazy."""
    return IteratorI(ReversedOp(iterable))


def Flatten(iterable: object) -> IteratorI:  # noqa: N802
    """Flatten one level of nesting. Lazy."""
    return IteratorI(FlattenOp(iterable))


def Unique(iterable: object, *, key: Callable | None = None) -> IteratorI:  # noqa: N802
    """Unique elements preserving order. Lazy."""
    return IteratorI(UniqueOp(iterable, key))


def Pluck(iterable: object, field: object) -> IteratorI:  # noqa: N802
    """Extract field from each element. Lazy."""
    return IteratorI(PluckOp(iterable, field))


def FilterBy(iterable: object, field: object, value: object) -> IteratorI:  # noqa: N802
    """Filter elements where field equals value. Lazy."""
    return IteratorI(FilterByOp(iterable, field, value))


def Sorted(iterable: object, *, reverse: object = False) -> ListI:  # noqa: N802
    """Sorted iterable. Terminal — inherently eager."""
    return ListI(SortedOp(iterable, reverse))


def ToDict(iterable: object, key_fn: Callable, val_fn: Callable) -> DictI:  # noqa: N802
    """Build dict from iterable using key/value extractors. Terminal."""
    return DictI(ToDictOp(iterable, key_fn, val_fn))
