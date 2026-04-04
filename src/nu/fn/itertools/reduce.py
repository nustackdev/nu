"""Iterable reductions — Value-returning factories over op Ops.

Reduce, Sum, Min, Max (eager -> AnyI)
Any, All (eager -> BoolI)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.interfaces import AnyI, BoolI
from nu.ops.itertools.reduce import AllOp, AnyOp, MaxOp, MinOp, ReduceOp, SumOp


if TYPE_CHECKING:
    from collections.abc import Callable


__all__ = [
    "All",
    "Any",
    "Max",
    "Min",
    "Reduce",
    "Sum",
]


def Reduce(iterable: object, fn: Callable, initial: object) -> AnyI:  # noqa: N802
    """Reduce iterable to single value. Terminal."""
    return AnyI(ReduceOp(iterable, fn, initial))


def Sum(iterable: object) -> AnyI:  # noqa: N802
    """Sum all elements. Terminal."""
    return AnyI(SumOp(iterable))


def Min(iterable: object, *, key: Callable | None = None) -> AnyI:  # noqa: N802
    """Get minimum element. Terminal."""
    return AnyI(MinOp(iterable, key))


def Max(iterable: object, *, key: Callable | None = None) -> AnyI:  # noqa: N802
    """Get maximum element. Terminal."""
    return AnyI(MaxOp(iterable, key))


def Any(iterable: object) -> BoolI:  # noqa: N802
    """Check if any element is truthy. Terminal."""
    return BoolI(AnyOp(iterable))


def All(iterable: object) -> BoolI:  # noqa: N802
    """Check if all elements are truthy. Terminal."""
    return BoolI(AllOp(iterable))
