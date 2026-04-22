"""Iterable combination ops — Zip, Chain, Enumerate. Lazy iterators."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from itertools import chain
from typing import Any

from nu.terms import INVALID, BinaryScalar, NAryScalar, Sentinel


__all__ = [
    "Chain",
    "Enumerate",
    "Zip",
]


class Zip(NAryScalar[Iterator[tuple]]):
    """Zip multiple iterables: zip(*iterables) -> lazy iterator."""

    def __init__(self, *operands: object) -> None:
        """Initialize with 2+ iterables."""
        NAryScalar.__init__(self, *operands)

    def apply(self, *values: Any) -> Iterator[tuple] | Sentinel:
        """Apply: zip resolved iterables lazily."""
        for v in values:
            if isinstance(v, Sentinel):
                return INVALID
        return zip(*values, strict=False)

    def __repr__(self) -> str:
        args = ", ".join(repr(c) for c in self._children)
        return f"Zip({args})"


class Chain(NAryScalar[Iterator]):
    """Chain multiple iterables: chain(*iterables) -> lazy iterator."""

    def __init__(self, *operands: object) -> None:
        """Initialize with 2+ iterables."""
        NAryScalar.__init__(self, *operands)

    def apply(self, *values: Any) -> Iterator | Sentinel:
        """Apply: chain resolved iterables lazily."""
        for v in values:
            if isinstance(v, Sentinel):
                return INVALID
        return chain(*values)

    def __repr__(self) -> str:
        args = ", ".join(repr(c) for c in self._children)
        return f"Chain({args})"


class Enumerate(BinaryScalar[Iterator[tuple[int, object]]]):
    """Enumerate iterable: enumerate(iterable, start) -> lazy iterator."""

    def apply(self, left: object, right: object) -> Iterator[tuple[int, object]] | Sentinel:
        """Apply: left=iterable, right=start."""
        if not isinstance(left, Iterable):
            raise TypeError(f"Enumerate requires iterable, got {type(left).__name__}")
        return enumerate(left, start=int(right))  # type: ignore

    def __repr__(self) -> str:
        return f"Enumerate({self._children[0]!r}, start={self._children[1]!r})"
