"""Iterable transformations — Value-returning factories over morphism Ops.

Map, Filter, Reversed, Flatten, Unique, Pluck, FilterBy (lazy -> IteratorValue)
Sorted (eager -> ListValue)
ToDict (eager -> DictValue)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...morphisms.itertools.transform import (
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
from ...values import DictValue, IteratorValue, ListValue


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


def Map(iterable: object, fn: Callable) -> IteratorValue:  # noqa: N802
    """Map function over iterable elements. Lazy."""
    return IteratorValue(MapOp(iterable, fn))


def Filter(iterable: object, predicate: Callable) -> IteratorValue:  # noqa: N802
    """Filter iterable by predicate. Lazy."""
    return IteratorValue(FilterOp(iterable, predicate))


def Reversed(iterable: object) -> IteratorValue:  # noqa: N802
    """Reversed sequence. Lazy."""
    return IteratorValue(ReversedOp(iterable))


def Flatten(iterable: object) -> IteratorValue:  # noqa: N802
    """Flatten one level of nesting. Lazy."""
    return IteratorValue(FlattenOp(iterable))


def Unique(iterable: object, *, key: Callable | None = None) -> IteratorValue:  # noqa: N802
    """Unique elements preserving order. Lazy."""
    return IteratorValue(UniqueOp(iterable, key))


def Pluck(iterable: object, field: object) -> IteratorValue:  # noqa: N802
    """Extract field from each element. Lazy."""
    return IteratorValue(PluckOp(iterable, field))


def FilterBy(iterable: object, field: object, value: object) -> IteratorValue:  # noqa: N802
    """Filter elements where field equals value. Lazy."""
    return IteratorValue(FilterByOp(iterable, field, value))


def Sorted(iterable: object, *, reverse: object = False) -> ListValue:  # noqa: N802
    """Sorted iterable. Terminal — inherently eager."""
    return ListValue(SortedOp(iterable, reverse))


def ToDict(iterable: object, key_fn: Callable, val_fn: Callable) -> DictValue:  # noqa: N802
    """Build dict from iterable using key/value extractors. Terminal."""
    return DictValue(ToDictOp(iterable, key_fn, val_fn))
