"""Iterable slicing — Value-returning factories over morphism Ops.

Take, Drop (lazy -> IteratorValue)
"""

from __future__ import annotations

from ...morphisms.itertools.slice import DropOp, TakeOp
from ...values import IteratorValue


__all__ = [
    "Drop",
    "Take",
]


def Take(iterable: object, n: object) -> IteratorValue:  # noqa: N802
    """Take first N elements. Lazy."""
    return IteratorValue(TakeOp(iterable, n))


def Drop(iterable: object, n: object) -> IteratorValue:  # noqa: N802
    """Drop first N elements. Lazy."""
    return IteratorValue(DropOp(iterable, n))
