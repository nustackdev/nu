"""Iterable combination ops — Zip, Chain, Enumerate. Lazy iterators."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from itertools import chain

from nu.terms import INVALID, BinaryCalc, Sentinel
from nu.terms.op import NAryOp, Calculation


__all__ = [
    "ChainOp",
    "EnumerateOp",
    "ZipOp",
]


class ZipOp(Calculation, NAryOp[Iterator[tuple]]):
    """Zip multiple iterables: zip(*iterables) -> lazy iterator."""

    def __init__(self, *operands: object) -> None:
        """Initialize with 2+ iterables."""
        NAryOp.__init__(self, *operands)

    async def execute(self, ctx: object) -> Iterator[tuple] | Sentinel:
        """Execute — resolve all operands and zip lazily."""
        values = []
        for child in self._children:
            val = await child.execute(ctx)
            if isinstance(val, Sentinel):
                return INVALID
            values.append(val)
        return zip(*values, strict=False)

    def __repr__(self) -> str:
        args = ", ".join(repr(c) for c in self._children)
        return f"ZipOp({args})"


class ChainOp(Calculation, NAryOp[Iterator]):
    """Chain multiple iterables: chain(*iterables) -> lazy iterator."""

    def __init__(self, *operands: object) -> None:
        """Initialize with 2+ iterables."""
        NAryOp.__init__(self, *operands)

    async def execute(self, ctx: object) -> Iterator | Sentinel:
        """Execute — resolve all operands and chain lazily."""
        values = []
        for child in self._children:
            val = await child.execute(ctx)
            if isinstance(val, Sentinel):
                return INVALID
            values.append(val)
        return chain(*values)

    def __repr__(self) -> str:
        args = ", ".join(repr(c) for c in self._children)
        return f"ChainOp({args})"


class EnumerateOp(BinaryCalc[Iterator[tuple[int, object]]]):
    """Enumerate iterable: enumerate(iterable, start) -> lazy iterator."""

    def apply(self, left: object, right: object) -> Iterator[tuple[int, object]] | Sentinel:
        """Apply: left=iterable, right=start."""
        if not isinstance(left, Iterable):
            raise TypeError(f"Enumerate requires iterable, got {type(left).__name__}")
        return enumerate(left, start=int(right))  # type: ignore

    def __repr__(self) -> str:
        return f"EnumerateOp({self._children[0]!r}, start={self._children[1]!r})"
