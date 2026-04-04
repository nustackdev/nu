"""Iterable grouping — Value-returning factories over op Ops.

GroupBy (eager -> ListI)
Partition (eager -> TupleI)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.interfaces import ListI, TupleI
from nu.ops.itertools.group import GroupByOp, PartitionOp


if TYPE_CHECKING:
    from collections.abc import Callable


__all__ = [
    "GroupBy",
    "Partition",
]


def GroupBy(iterable: object, key_fn: Callable) -> ListI:  # noqa: N802
    """Group elements by key function. Terminal."""
    return ListI(GroupByOp(iterable, key_fn))


def Partition(iterable: object, predicate: Callable) -> TupleI:  # noqa: N802
    """Partition into (matches, non_matches). Terminal."""
    return TupleI(PartitionOp(iterable, predicate))
