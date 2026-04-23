"""Iteration Flow Commands -- ForRange, ForEach."""

from __future__ import annotations

from contextlib import aclosing, closing
from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms import Flow, Mode


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator

    from nu.context import Context
    from nu.terms import IntArg, Nu, StrArg


__all__ = [
    "ForEach",
    "ForRange",
]


class ForRange(Flow):
    """Counted loop over ``range(start, stop, step)``.

    Children: ``[start, stop, step, body]``
    Children (with index): ``[start, stop, step, body, index]``

    Sets ``ctx.attrs[index]`` to the current loop value each iteration.
    """

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.BOTH

    def __init__(
        self,
        start: IntArg,
        stop: IntArg,
        body: Nu,
        *,
        step: IntArg = 1,
        index: StrArg | None = None,
    ) -> None:
        self._has_index = index is not None
        children: list = [start, stop, step, body]
        if index is not None:
            children.append(index)
        super().__init__(*children)

    async def aopen(self, ctx: Context) -> AsyncGenerator[Any, None]:
        """Execute body for each i in range(start, stop, step)."""
        start = await self.children[0].afirst(ctx)
        stop = await self.children[1].afirst(ctx)
        step = await self.children[2].afirst(ctx)
        body = self.children[3]

        index_key: str | None = None
        if self._has_index:
            index_key = await self.children[4].afirst(ctx)

        for i in range(start, stop, step):
            if index_key is not None:
                ctx.attrs[index_key] = i
            async with aclosing(body.aopen(ctx)) as gen:
                async for v in gen:
                    yield v

    def open(self, ctx: Context) -> Generator[Any, None, None]:
        start = self.children[0].first(ctx)
        stop = self.children[1].first(ctx)
        step = self.children[2].first(ctx)
        body = self.children[3]

        index_key: str | None = None
        if self._has_index:
            index_key = self.children[4].first(ctx)

        for i in range(start, stop, step):
            if index_key is not None:
                ctx.attrs[index_key] = i
            with closing(body.open(ctx)) as gen:
                yield from gen


class ForEach(Flow):
    """Iterate over a sequence, executing body for each element.

    Children: ``[items, body, item?, index?]``

    Sets ``ctx.attrs[item]`` to the current element and optionally
    ``ctx.attrs[index]`` to the current iteration count.
    """

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.BOTH

    def __init__(
        self,
        items: Any,
        body: Nu,
        *,
        item: StrArg | None = None,
        index: StrArg | None = None,
    ) -> None:
        self._has_item = item is not None
        self._has_index = index is not None
        children: list = [items, body]
        if item is not None:
            children.append(item)
        if index is not None:
            children.append(index)
        super().__init__(*children)

    async def aopen(self, ctx: Context) -> AsyncGenerator[Any, None]:
        """Execute body for each element of items."""
        body = self.children[1]

        child_idx = 2
        item_key: str | None = None
        index_key: str | None = None
        if self._has_item:
            item_key = await self.children[child_idx].afirst(ctx)
            child_idx += 1
        if self._has_index:
            index_key = await self.children[child_idx].afirst(ctx)

        # Keep items generator open across body iterations so any scope
        # opened by the items subtree (e.g. Snapshot) stays alive while
        # the body reads from its view.
        async with aclosing(self.children[0].aopen(ctx)) as items_gen:
            async for items in items_gen:
                for i, elem in enumerate(items):
                    if item_key is not None:
                        ctx.attrs[item_key] = elem
                    if index_key is not None:
                        ctx.attrs[index_key] = i
                    async with aclosing(body.aopen(ctx)) as gen:
                        async for v in gen:
                            yield v

    def open(self, ctx: Context) -> Generator[Any, None, None]:
        body = self.children[1]

        child_idx = 2
        item_key: str | None = None
        index_key: str | None = None
        if self._has_item:
            item_key = self.children[child_idx].first(ctx)
            child_idx += 1
        if self._has_index:
            index_key = self.children[child_idx].first(ctx)

        with closing(self.children[0].open(ctx)) as items_gen:
            for items in items_gen:
                for i, elem in enumerate(items):
                    if item_key is not None:
                        ctx.attrs[item_key] = elem
                    if index_key is not None:
                        ctx.attrs[index_key] = i
                    with closing(body.open(ctx)) as gen:
                        yield from gen
