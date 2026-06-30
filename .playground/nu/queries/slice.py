"""Iterable slicing ops - Take, Drop. Lazy iterators."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from itertools import islice
from typing import Any, ClassVar

from nu.terms.query import ScalarQuery
from nu.terms.sentinels import INVALID
from nu.terms.types import Mode


__all__ = [
    "Drop",
    "Take",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class Take(ScalarQuery):
    """Take first N elements."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, iterable: Any, n: Any) -> None:  # noqa: ANN401
        super().__init__(iterable, n)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        left, right = ops
        if not isinstance(left, Iterable):
            msg = f"Take requires iterable, got {type(left).__name__}"
            raise TypeError(msg)
        try:
            return islice(left, int(right))
        except (TypeError, ValueError):
            return INVALID


class Drop(ScalarQuery):
    """Drop first N elements."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, iterable: Any, n: Any) -> None:  # noqa: ANN401
        super().__init__(iterable, n)

    def _apply(self, ctx: Any, ops: list[Any]) -> Iterator:  # noqa: ANN401
        left, right = ops
        if not isinstance(left, Iterable):
            msg = f"Drop requires iterable, got {type(left).__name__}"
            raise TypeError(msg)
        try:
            return islice(left, int(right), None)
        except (TypeError, ValueError):
            return INVALID
