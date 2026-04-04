"""Iterable slicing — Value-returning factories over op Ops.

Take, Drop (lazy -> IteratorI)
"""

from __future__ import annotations

from nu.interfaces import IteratorI
from nu.ops.itertools.slice import DropOp, TakeOp


__all__ = [
    "Drop",
    "Take",
]


def Take(iterable: object, n: object) -> IteratorI:  # noqa: N802
    """Take first N elements. Lazy."""
    return IteratorI(TakeOp(iterable, n))


def Drop(iterable: object, n: object) -> IteratorI:  # noqa: N802
    """Drop first N elements. Lazy."""
    return IteratorI(DropOp(iterable, n))
