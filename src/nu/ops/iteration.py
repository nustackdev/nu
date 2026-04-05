"""Iteration ops -- ForRange, ForEach, Fold."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from nu.terms.op import Calculation


if TYPE_CHECKING:
    from nu.context import Context
    from nu.terms import IntArg, Nu, StrArg


__all__ = [
    "Fold",
    "ForEach",
    "ForRange",
]


class ForRange(Calculation):
    """Counted loop over ``range(start, stop, step)``.

    Children: ``[start, stop, step, body]``
    Children (with index): ``[start, stop, step, body, index]``

    Sets ``ctx.attrs[index]`` to the current loop value each iteration.
    """

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

    async def execute(self, ctx: Context) -> None:
        start = await self.children[0].execute(ctx)
        stop = await self.children[1].execute(ctx)
        step = await self.children[2].execute(ctx)
        body = self.children[3]

        index_key: str | None = None
        if self._has_index:
            index_key = await self.children[4].execute(ctx)

        for i in range(start, stop, step):
            if index_key is not None:
                ctx.attrs[index_key] = i
            await body.execute(ctx)


class ForEach(Calculation):
    """Iterate over a sequence, executing body for each element.

    Children: ``[items, body, item?, index?]``

    Sets ``ctx.attrs[item]`` to the current element and optionally
    ``ctx.attrs[index]`` to the current iteration count.
    """

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

    async def execute(self, ctx: Context) -> None:
        items = await self.children[0].execute(ctx)
        body = self.children[1]

        child_idx = 2
        item_key: str | None = None
        index_key: str | None = None
        if self._has_item:
            item_key = await self.children[child_idx].execute(ctx)
            child_idx += 1
        if self._has_index:
            index_key = await self.children[child_idx].execute(ctx)

        for i, elem in enumerate(items):
            if item_key is not None:
                ctx.attrs[item_key] = elem
            if index_key is not None:
                ctx.attrs[index_key] = i
            await body.execute(ctx)


class Fold(Calculation):
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

    async def execute(self, ctx: Context) -> None:
        items = await self.children[0].execute(ctx)
        initial = await self.children[1].execute(ctx)
        body = self.children[2]
        acc_key: str = await self.children[3].execute(ctx)
        item_key: str = await self.children[4].execute(ctx)

        ctx.attrs[acc_key] = initial

        for elem in items:
            ctx.attrs[item_key] = elem
            await body.execute(ctx)
