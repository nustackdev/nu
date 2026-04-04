"""Collection iteration ops -- Nu-native iteration over collections.

Every predicate/transform is a Nu -- no lambdas, no holes in the tree.
Deformations see everything.

Pattern: items + Nu expression(s) + body/output + item key.
Items are set on ctx.attrs[item] each iteration so the body and
condition/transform Nus can read them via AttrRef.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from nu.terms.op import Calculation


if TYPE_CHECKING:
    from nu.context import Context
    from nu.terms import Arg, Nu, StrArg


__all__ = [
    "Filter",
    "Map",
    "TakeWhile",
    "Unique",
]


class Filter(Calculation):
    """Execute body for each item where condition is truthy.

    Children: ``[items, condition, body, item_key]``
    """

    def __init__(
        self,
        items: Arg[Iterable],
        *,
        condition: Nu,
        body: Nu,
        item: StrArg = "item",
    ) -> None:
        super().__init__(items, condition, body, item)

    async def execute(self, ctx: Context) -> None:
        items = await self.children[0].execute(ctx)
        condition = self.children[1]
        body = self.children[2]
        item_key: str = await self.children[3].execute(ctx)

        for elem in items:
            ctx.attrs[item_key] = elem
            if await condition.execute(ctx):
                await body.execute(ctx)


class Map(Calculation):
    """Transform each item via a Nu expression, collect results.

    Children: ``[items, transform, item_key, output_key]``

    Results stored in ``ctx.attrs[output]`` as a list.
    """

    def __init__(
        self,
        items: Arg[Iterable],
        *,
        transform: Nu,
        output: StrArg = "result",
        item: StrArg = "item",
    ) -> None:
        super().__init__(items, transform, item, output)

    async def execute(self, ctx: Context) -> None:
        items = await self.children[0].execute(ctx)
        transform = self.children[1]
        item_key: str = await self.children[2].execute(ctx)
        output_key: str = await self.children[3].execute(ctx)

        results = []
        for elem in items:
            ctx.attrs[item_key] = elem
            results.append(await transform.execute(ctx))
        ctx.attrs[output_key] = results


class TakeWhile(Calculation):
    """Execute body while condition holds. Stop on first false.

    Children: ``[items, condition, body, item_key]``
    """

    def __init__(
        self,
        items: Arg[Iterable],
        *,
        condition: Nu,
        body: Nu,
        item: StrArg = "item",
    ) -> None:
        super().__init__(items, condition, body, item)

    async def execute(self, ctx: Context) -> None:
        items = await self.children[0].execute(ctx)
        condition = self.children[1]
        body = self.children[2]
        item_key: str = await self.children[3].execute(ctx)

        for elem in items:
            ctx.attrs[item_key] = elem
            if not await condition.execute(ctx):
                break
            await body.execute(ctx)


class Unique(Calculation):
    """Execute body for each item with a unique key.

    Children: ``[items, key, body, item_key]``
    """

    def __init__(
        self,
        items: Arg[Iterable],
        *,
        key: Nu,
        body: Nu,
        item: StrArg = "item",
    ) -> None:
        super().__init__(items, key, body, item)

    async def execute(self, ctx: Context) -> None:
        items = await self.children[0].execute(ctx)
        key_expr = self.children[1]
        body = self.children[2]
        item_key: str = await self.children[3].execute(ctx)

        seen: set = set()
        for elem in items:
            ctx.attrs[item_key] = elem
            k = await key_expr.execute(ctx)
            if k not in seen:
                seen.add(k)
                await body.execute(ctx)
