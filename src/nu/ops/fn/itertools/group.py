"""Iterable grouping — Value-returning factories over morphism Ops.

GroupBy (eager -> ListValue)
Partition (eager -> TupleValue)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.ops.itertools.group import GroupByOp, PartitionOp
from nu.interfaces.values import ListValue, TupleValue


if TYPE_CHECKING:
    from collections.abc import Callable


__all__ = [
    "GroupBy",
    "Partition",
]


def GroupBy(iterable: object, key_fn: Callable) -> ListValue:  # noqa: N802
    """Group elements by key function. Terminal."""
    return ListValue(GroupByOp(iterable, key_fn))


def Partition(iterable: object, predicate: Callable) -> TupleValue:  # noqa: N802
    """Partition into (matches, non_matches). Terminal."""
    return TupleValue(PartitionOp(iterable, predicate))
