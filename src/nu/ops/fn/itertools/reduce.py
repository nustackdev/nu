"""Iterable reductions — Value-returning factories over op Ops.

Reduce, Sum, Min, Max (eager -> AnyValue)
Any, All (eager -> BoolValue)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.ops.itertools.reduce import AllOp, AnyOp, MaxOp, MinOp, ReduceOp, SumOp
from nu.interfaces.values import AnyValue, BoolValue


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


def Reduce(iterable: object, fn: Callable, initial: object) -> AnyValue:  # noqa: N802
    """Reduce iterable to single value. Terminal."""
    return AnyValue(ReduceOp(iterable, fn, initial))


def Sum(iterable: object) -> AnyValue:  # noqa: N802
    """Sum all elements. Terminal."""
    return AnyValue(SumOp(iterable))


def Min(iterable: object, *, key: Callable | None = None) -> AnyValue:  # noqa: N802
    """Get minimum element. Terminal."""
    return AnyValue(MinOp(iterable, key))


def Max(iterable: object, *, key: Callable | None = None) -> AnyValue:  # noqa: N802
    """Get maximum element. Terminal."""
    return AnyValue(MaxOp(iterable, key))


def Any(iterable: object) -> BoolValue:  # noqa: N802
    """Check if any element is truthy. Terminal."""
    return BoolValue(AnyOp(iterable))


def All(iterable: object) -> BoolValue:  # noqa: N802
    """Check if all elements are truthy. Terminal."""
    return BoolValue(AllOp(iterable))
