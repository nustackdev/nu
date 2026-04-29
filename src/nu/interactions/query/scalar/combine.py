"""Iterable combination ops - Zip, Chain, Enumerate. Lazy iterators."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from itertools import chain
from typing import Any, ClassVar

from nu.terms.query import ScalarQuery
from nu.terms.types import Mode


__all__ = [
    "Chain",
    "Enumerate",
    "Zip",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class Zip(ScalarQuery):
    """Zip multiple iterables: zip(*iterables) -> lazy iterator."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, *operands: Any) -> None:  # noqa: ANN401
        super().__init__(*operands)

    def _apply(self, ctx: Any, ops: list[Any]) -> Iterator[tuple]:  # noqa: ANN401
        return zip(*ops, strict=False)


class Chain(ScalarQuery):
    """Chain multiple iterables: chain(*iterables) -> lazy iterator."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, *operands: Any) -> None:  # noqa: ANN401
        super().__init__(*operands)

    def _apply(self, ctx: Any, ops: list[Any]) -> Iterator:  # noqa: ANN401
        return chain(*ops)


class Enumerate(ScalarQuery):
    """Enumerate iterable: enumerate(iterable, start) -> lazy iterator."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, iterable: Any, start: Any) -> None:  # noqa: ANN401
        super().__init__(iterable, start)

    def _apply(self, ctx: Any, ops: list[Any]) -> Iterator[tuple[int, object]]:  # noqa: ANN401
        left, right = ops
        if not isinstance(left, Iterable):
            msg = f"Enumerate requires iterable, got {type(left).__name__}"
            raise TypeError(msg)
        return enumerate(left, start=int(right))
