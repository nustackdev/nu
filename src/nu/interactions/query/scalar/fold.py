"""Fold — stateful sequential reduction over an iterable.

Stream Query: yields per-iteration values from the body while threading
an accumulator through ctx.attrs.
"""

from __future__ import annotations

from contextlib import aclosing, closing
from typing import TYPE_CHECKING, Any

from nu.terms import Stream


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

    async def open(self, ctx: Context) -> AsyncGenerator[Any, None]:
        """Execute body for each element, threading acc through ctx.attrs."""
        initial = await self.children[1].first(ctx)
        body = self.children[2]
        acc_key: str = await self.children[3].first(ctx)
        item_key: str = await self.children[4].first(ctx)

        ctx.attrs[acc_key] = initial

        # Keep items generator open so any scope opened by the items
        # subtree (e.g. Snapshot) stays alive while the body reads from it.
        async with aclosing(self.children[0].open(ctx)) as items_gen:
            async for items in items_gen:
                for elem in items:
                    ctx.attrs[item_key] = elem
                    async with aclosing(body.open(ctx)) as gen:
                        async for v in gen:
                            yield v

    def open_sync(self, ctx: Context) -> Generator[Any, None, None]:
        initial = self.children[1].first_sync(ctx)
        body = self.children[2]
        acc_key: str = self.children[3].first_sync(ctx)
        item_key: str = self.children[4].first_sync(ctx)

        ctx.attrs[acc_key] = initial

        with closing(self.children[0].open_sync(ctx)) as items_gen:
            for items in items_gen:
                for elem in items:
                    ctx.attrs[item_key] = elem
                    with closing(body.open_sync(ctx)) as gen:
                        yield from gen
