"""Fold - stateful sequential reduction over an iterable.

Stream Query: yields per-iteration values from the body while threading
an accumulator through ctx.attrs.
"""

from __future__ import annotations

from contextlib import aclosing, closing
from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.query import StreamQuery
from nu.terms.types import Mode


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator


__all__ = ["Fold"]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class Fold(StreamQuery):
    """Stateful sequential reduction over an iterable.

    Children: ``[items, initial, body, acc, item]``
    """

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(
        self,
        items: Any,  # noqa: ANN401
        *,
        acc: Any = "acc",  # noqa: ANN401
        initial: Any,  # noqa: ANN401
        item: Any = "item",  # noqa: ANN401
        body: Any,  # noqa: ANN401
    ) -> None:
        super().__init__(items, initial, body, acc, item)

    async def aopen(self, ctx: Any) -> AsyncGenerator[Any, None]:  # type: ignore[override]
        from nu import runtime

        initial = await runtime.afirst(self._children[1], ctx)
        body = self._children[2]
        acc_key: str = await runtime.afirst(self._children[3], ctx)
        item_key: str = await runtime.afirst(self._children[4], ctx)

        ctx.attrs[acc_key] = initial

        items_first = await runtime.afirst(self._children[0], ctx)
        for elem in items_first:
            ctx.attrs[item_key] = elem
            async with aclosing(body.aopen(ctx)) as gen:
                async for v in gen:
                    yield v

    def open(self, ctx: Any) -> Generator[Any, None, None]:  # type: ignore[override]
        from nu import runtime

        initial = runtime.first(self._children[1], ctx)
        body = self._children[2]
        acc_key: str = runtime.first(self._children[3], ctx)
        item_key: str = runtime.first(self._children[4], ctx)

        ctx.attrs[acc_key] = initial

        items_first = runtime.first(self._children[0], ctx)
        for elem in items_first:
            ctx.attrs[item_key] = elem
            with closing(body.open(ctx)) as gen:
                yield from gen
