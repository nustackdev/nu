"""Reduction concretes - First, Last, Collect, Reduce.

Each is a ScalarQuery whose child is a StreamQuery. They drive the
child's stream via `open` / `aopen` and yield one value (or EMPTY).
"""

from __future__ import annotations

from typing import Any, ClassVar

from nu.terms.query import Reduction
from nu.terms.types import Mode


__all__ = [
    "Collect",
    "First",
    "Last",
    "Reduce",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class First(Reduction):
    """First yield of the child stream. EMPTY if the stream is empty."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def eval(self, ctx: Any) -> Any:  # noqa: ANN401, D102
        from nu.terms.sentinels import EMPTY

        child = self._children[0]
        for v in child.open(ctx):
            return v
        return EMPTY

    async def aeval(self, ctx: Any) -> Any:  # noqa: ANN401, D102
        from nu.terms.sentinels import EMPTY

        child = self._children[0]
        async for v in child.aopen(ctx):
            return v
        return EMPTY


class Last(Reduction):
    """Last yield of the child stream. EMPTY if the stream is empty."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def eval(self, ctx: Any) -> Any:  # noqa: ANN401, D102
        from nu.terms.sentinels import EMPTY

        child = self._children[0]
        found = False
        last: Any = None
        for v in child.open(ctx):
            last = v
            found = True
        return last if found else EMPTY

    async def aeval(self, ctx: Any) -> Any:  # noqa: ANN401, D102
        from nu.terms.sentinels import EMPTY

        child = self._children[0]
        found = False
        last: Any = None
        async for v in child.aopen(ctx):
            last = v
            found = True
        return last if found else EMPTY


class Collect(Reduction):
    """Drain the child stream into a list."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def eval(self, ctx: Any) -> list[Any]:  # noqa: D102
        return list(self._children[0].open(ctx))

    async def aeval(self, ctx: Any) -> list[Any]:  # noqa: D102
        out: list[Any] = []
        async for v in self._children[0].aopen(ctx):
            out.append(v)
        return out


class Reduce(Reduction):
    """Fold the child stream with a Python callable.

    `Reduce(stream_q, fn, initial=...)` - fn is plain callable, not a Nu.
    """

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(
        self,
        stream: Any,  # noqa: ANN401
        fn: Any,  # noqa: ANN401
        initial: Any = None,  # noqa: ANN401
    ) -> None:
        super().__init__(stream)
        self._fn = fn
        self._initial = initial

    def eval(self, ctx: Any) -> Any:  # noqa: ANN401, D102
        acc = self._initial
        for v in self._children[0].open(ctx):
            acc = self._fn(acc, v)
        return acc

    async def aeval(self, ctx: Any) -> Any:  # noqa: ANN401, D102
        acc = self._initial
        async for v in self._children[0].aopen(ctx):
            acc = self._fn(acc, v)
        return acc
