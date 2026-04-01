"""Iterable combinators — Value-returning factories over morphism Ops.

Zip, Chain, Enumerate (lazy -> IteratorValue)
"""

from __future__ import annotations

from nu.ops.itertools.combine import ChainOp, EnumerateOp, ZipOp
from nu.interfaces.values import IteratorValue


__all__ = [
    "Chain",
    "Enumerate",
    "Zip",
]


def Zip(*iterables: object) -> IteratorValue:  # noqa: N802
    """Zip multiple iterables together. Lazy."""
    return IteratorValue(ZipOp(*iterables))


def Chain(*iterables: object) -> IteratorValue:  # noqa: N802
    """Chain multiple iterables into one. Lazy."""
    return IteratorValue(ChainOp(*iterables))


def Enumerate(iterable: object, start: object = 0) -> IteratorValue:  # noqa: N802
    """Enumerate iterable with index. Lazy."""
    return IteratorValue(EnumerateOp(iterable, start))
