"""Iterable reductions — Value-returning factories over op Ops.

Sum, Min, Max (eager -> AnyI)
Any, All (eager -> BoolI)
"""

from __future__ import annotations

from nu.ops import AllOp, AnyOp, MaxOp, MinOp, SumOp
from nu.primitives import AnyI, BoolI


__all__ = [
    "All",
    "Any",
    "Max",
    "Min",
    "Sum",
]


def Sum(iterable: object) -> AnyI:  # noqa: N802
    """Sum all elements. Terminal."""
    return AnyI(SumOp(iterable))


def Min(iterable: object) -> AnyI:  # noqa: N802
    """Get minimum element. Terminal."""
    return AnyI(MinOp(iterable))


def Max(iterable: object) -> AnyI:  # noqa: N802
    """Get maximum element. Terminal."""
    return AnyI(MaxOp(iterable))


def Any(iterable: object) -> BoolI:  # noqa: N802
    """Check if any element is truthy. Terminal."""
    return BoolI(AnyOp(iterable))


def All(iterable: object) -> BoolI:  # noqa: N802
    """Check if all elements are truthy. Terminal."""
    return BoolI(AllOp(iterable))
