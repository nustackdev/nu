"""Iterable combination morphisms — Zip, Chain, Enumerate."""

from __future__ import annotations

from collections.abc import Iterable
from itertools import chain

from everybase.core import INVALID, BinaryOperation, Sentinel
from everybase.core.term.morphism import NAryMorphism, Operation


__all__ = [
    "ChainOp",
    "EnumerateOp",
    "ZipOp",
]


class ZipOp(Operation, NAryMorphism[list[tuple]]):
    """Zip multiple iterables: list(zip(*iterables))."""

    def __init__(self, *operands: object) -> None:
        """Initialize with 2+ iterables."""
        NAryMorphism.__init__(self, *operands)

    async def execute(self, ctx: object) -> list[tuple] | Sentinel:
        """Execute — resolve all operands and zip."""
        values = []
        for child in self._children:
            val = await child.execute(ctx)
            if isinstance(val, Sentinel):
                return INVALID
            values.append(val)
        return list(zip(*values, strict=False))

    def __repr__(self) -> str:
        args = ", ".join(repr(c) for c in self._children)
        return f"ZipOp({args})"


class ChainOp(Operation, NAryMorphism[list]):
    """Chain multiple iterables: list(chain(*iterables))."""

    def __init__(self, *operands: object) -> None:
        """Initialize with 2+ iterables."""
        NAryMorphism.__init__(self, *operands)

    async def execute(self, ctx: object) -> list | Sentinel:
        """Execute — resolve all operands and chain."""
        values = []
        for child in self._children:
            val = await child.execute(ctx)
            if isinstance(val, Sentinel):
                return INVALID
            values.append(val)
        return list(chain(*values))

    def __repr__(self) -> str:
        args = ", ".join(repr(c) for c in self._children)
        return f"ChainOp({args})"


class EnumerateOp(BinaryOperation[list[tuple[int, object]]]):
    """Enumerate iterable: list(enumerate(iterable, start))."""

    def apply(self, left: object, right: object) -> list[tuple[int, object]] | Sentinel:
        """Apply: left=iterable, right=start."""
        if not isinstance(left, Iterable):
            raise TypeError(f"Enumerate requires iterable, got {type(left).__name__}")
        return list(enumerate(left, start=int(right)))  # type: ignore

    def __repr__(self) -> str:
        return f"EnumerateOp({self._children[0]!r}, start={self._children[1]!r})"
