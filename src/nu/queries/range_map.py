"""MapRange - query twin of ForRangeDo.

Walks an integer range, evaluates a Nu body query per index, and
yields the flat concatenation of per-step results as a stream.

Body reads the current index via `ctx.attrs[item_key]` (mirror of
ForRangeDo's `index` binding).
"""

from __future__ import annotations

from contextlib import aclosing, closing
from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.query import StreamQuery
from nu.terms.types import Mode


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator

    from nu.terms import IntArg, Nu, StrArg


__all__ = ["MapRange"]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class MapRange(StreamQuery):
    """Map an index range through a body query, flat-concat results.

    For each `i in range(start, stop, step)`, binds `ctx.attrs[item]`
    to `i` and evaluates `body`. If `body` is a stream-shaped query its
    yields are drained per step; if it is a scalar-shaped query its
    value is yielded once per step. All per-step outputs are
    concatenated into one flat stream.

    Children: `[start, stop, step, body, item]`.
    """

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(
        self,
        start: IntArg,
        stop: IntArg,
        body: Nu,
        *,
        step: IntArg = 1,
        item: StrArg = "index",
    ) -> None:
        super().__init__(start, stop, step, body, item)

    def open(self, ctx: Any) -> Generator[Any, None, None]:  # noqa: ANN401, D102
        from nu import runtime

        start = runtime.first(self._children[0], ctx)
        stop = runtime.first(self._children[1], ctx)
        step = runtime.first(self._children[2], ctx)
        body = self._children[3]
        item_key: str = runtime.first(self._children[4], ctx)

        opener = getattr(body, "open", None)
        for i in range(start, stop, step):
            ctx.attrs[item_key] = i
            if opener is not None:
                with closing(opener(ctx)) as gen:
                    yield from gen
            else:
                yield runtime.first(body, ctx)

    async def aopen(self, ctx: Any) -> AsyncGenerator[Any, None]:  # noqa: ANN401, D102
        from nu import runtime

        start = await runtime.afirst(self._children[0], ctx)
        stop = await runtime.afirst(self._children[1], ctx)
        step = await runtime.afirst(self._children[2], ctx)
        body = self._children[3]
        item_key: str = await runtime.afirst(self._children[4], ctx)

        aopener = getattr(body, "aopen", None)
        for i in range(start, stop, step):
            ctx.attrs[item_key] = i
            if aopener is not None:
                async with aclosing(aopener(ctx)) as gen:
                    async for v in gen:
                        yield v
            else:
                yield await runtime.afirst(body, ctx)
