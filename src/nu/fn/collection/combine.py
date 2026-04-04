"""Iterable combinators — Value-returning factories over op Ops.

Zip, Chain, Enumerate (lazy -> IteratorI)
"""

from __future__ import annotations

from nu.interfaces import IteratorI
from nu.ops.collection.combine import ChainOp, EnumerateOp, ZipOp


__all__ = [
    "Chain",
    "Enumerate",
    "Zip",
]


def Zip(*iterables: object) -> IteratorI:  # noqa: N802
    """Zip multiple iterables together. Lazy."""
    return IteratorI(ZipOp(*iterables))


def Chain(*iterables: object) -> IteratorI:  # noqa: N802
    """Chain multiple iterables into one. Lazy."""
    return IteratorI(ChainOp(*iterables))


def Enumerate(iterable: object, start: object = 0) -> IteratorI:  # noqa: N802
    """Enumerate iterable with index. Lazy."""
    return IteratorI(EnumerateOp(iterable, start))
