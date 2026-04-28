"""Fold — stateful sequential reduction over an iterable.

Stream Query: yields per-iteration values from the body while threading
an accumulator through ctx.attrs.
"""

from __future__ import annotations

from contextlib import aclosing, closing
from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms import Mode, Stream


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator

    from nu.context import Context
    from nu.terms import Nu, StrArg


__all__ = ["Fold"]


class Fold(Stream):
    """Stateful sequential reduction over an iterable.

    Children: ``[items, initial, body, acc, item]``

    Sets ``ctx.attrs[acc]`` to the running accumulator and
    ``ctx.attrs[item]`` to the current element each iteration.
    """

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(
        self,
        items: Any,
        *,
        acc: StrArg = "acc",
        initial: Any,
        item: StrArg = "item",
        body: Nu,
    ) -> None:
        super().__init__(items, initial, body, acc, item)

    async def aopen(self, ctx: Context) -> AsyncGenerator[Any, None]:
        """Execute body for each element, threading acc through ctx.attrs."""
        initial = await self.children[1].afirst(ctx)
        body = self.children[2]
        acc_key: str = await self.children[3].afirst(ctx)
        item_key: str = await self.children[4].afirst(ctx)

        ctx.attrs[acc_key] = initial

        # Keep items generator open so any scope opened by the items
        # subtree (e.g. Snapshot) stays alive while the body reads from it.
        async with aclosing(self.children[0].aopen(ctx)) as items_gen:
            async for items in items_gen:
                for elem in items:
                    ctx.attrs[item_key] = elem
                    async with aclosing(body.aopen(ctx)) as gen:
                        async for v in gen:
                            yield v

    def open(self, ctx: Context) -> Generator[Any, None, None]:
        initial = self.children[1].first(ctx)
        body = self.children[2]
        acc_key: str = self.children[3].first(ctx)
        item_key: str = self.children[4].first(ctx)

        ctx.attrs[acc_key] = initial

        with closing(self.children[0].open(ctx)) as items_gen:
            for items in items_gen:
                for elem in items:
                    ctx.attrs[item_key] = elem
                    with closing(body.open(ctx)) as gen:
                        yield from gen
