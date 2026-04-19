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

from nu.terms.op import Command


if TYPE_CHECKING:
    from nu.context import Context
    from nu.terms import Arg, Nu, StrArg


__all__ = [
    "Filter",
    "Find",
    "FindIndex",
    "GroupBy",
    "Map",
    "Partition",
    "TakeWhile",
    "ToDict",
    "Unique",
]


class Filter(Command):
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

    async def run(self, ctx: Context) -> None:
        items = await self.children[0].first(ctx)
        condition = self.children[1]
        body = self.children[2]
        item_key: str = await self.children[3].first(ctx)

        for elem in items:
            ctx.attrs[item_key] = elem
            if await condition.first(ctx):
                await body.execute(ctx)


class Map(Command):
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

    async def run(self, ctx: Context) -> None:
        items = await self.children[0].first(ctx)
        transform = self.children[1]
        item_key: str = await self.children[2].first(ctx)
        output_key: str = await self.children[3].first(ctx)

        results = []
        for elem in items:
            ctx.attrs[item_key] = elem
            results.append(await transform.first(ctx))
        ctx.attrs[output_key] = results


class TakeWhile(Command):
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

    async def run(self, ctx: Context) -> None:
        items = await self.children[0].first(ctx)
        condition = self.children[1]
        body = self.children[2]
        item_key: str = await self.children[3].first(ctx)

        for elem in items:
            ctx.attrs[item_key] = elem
            if not await condition.first(ctx):
                break
            await body.execute(ctx)


class Unique(Command):
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

    async def run(self, ctx: Context) -> None:
        items = await self.children[0].first(ctx)
        key_expr = self.children[1]
        body = self.children[2]
        item_key: str = await self.children[3].first(ctx)

        seen: set = set()
        for elem in items:
            ctx.attrs[item_key] = elem
            k = await key_expr.first(ctx)
            if k not in seen:
                seen.add(k)
                await body.execute(ctx)


class Find(Command):
    """Find first item where condition is truthy.

    Children: ``[items, condition, item_key, output_key]``

    Stores the matching element in ``ctx.attrs[output]``.
    If no match, output is not set.
    """

    def __init__(
        self,
        items: Arg[Iterable],
        *,
        condition: Nu,
        output: StrArg = "found",
        item: StrArg = "item",
    ) -> None:
        super().__init__(items, condition, item, output)

    async def run(self, ctx: Context) -> None:
        items = await self.children[0].first(ctx)
        condition = self.children[1]
        item_key: str = await self.children[2].first(ctx)
        output_key: str = await self.children[3].first(ctx)

        for elem in items:
            ctx.attrs[item_key] = elem
            if await condition.first(ctx):
                ctx.attrs[output_key] = elem
                return


class FindIndex(Command):
    """Find index of first item where condition is truthy.

    Children: ``[items, condition, item_key, output_key]``

    Stores the index (int) in ``ctx.attrs[output]``.
    If no match, output is not set.
    """

    def __init__(
        self,
        items: Arg[Iterable],
        *,
        condition: Nu,
        output: StrArg = "found_index",
        item: StrArg = "item",
    ) -> None:
        super().__init__(items, condition, item, output)

    async def run(self, ctx: Context) -> None:
        items = await self.children[0].first(ctx)
        condition = self.children[1]
        item_key: str = await self.children[2].first(ctx)
        output_key: str = await self.children[3].first(ctx)

        for i, elem in enumerate(items):
            ctx.attrs[item_key] = elem
            if await condition.first(ctx):
                ctx.attrs[output_key] = i
                return


class GroupBy(Command):
    """Group items by a Nu key, execute body per group.

    Children: ``[items, key, body, item_key, group_key]``

    For each unique key value, collects all matching items into a list
    and sets ``ctx.attrs[group]`` to that list before executing body.
    """

    def __init__(
        self,
        items: Arg[Iterable],
        *,
        key: Nu,
        body: Nu,
        item: StrArg = "item",
        group: StrArg = "group",
    ) -> None:
        super().__init__(items, key, body, item, group)

    async def run(self, ctx: Context) -> None:
        items = await self.children[0].first(ctx)
        key_expr = self.children[1]
        body = self.children[2]
        item_key: str = await self.children[3].first(ctx)
        group_key: str = await self.children[4].first(ctx)

        groups: dict = {}
        for elem in items:
            ctx.attrs[item_key] = elem
            k = await key_expr.first(ctx)
            groups.setdefault(k, []).append(elem)

        for k, group_items in groups.items():
            ctx.attrs[item_key] = k
            ctx.attrs[group_key] = group_items
            await body.execute(ctx)


class Partition(Command):
    """Split items into matches and rest by a Nu condition.

    Children: ``[items, condition, item_key, matches_key, rest_key]``

    Stores matching items in ``ctx.attrs[matches]`` and
    non-matching in ``ctx.attrs[rest]``.
    """

    def __init__(
        self,
        items: Arg[Iterable],
        *,
        condition: Nu,
        matches: StrArg = "matches",
        rest: StrArg = "rest",
        item: StrArg = "item",
    ) -> None:
        super().__init__(items, condition, item, matches, rest)

    async def run(self, ctx: Context) -> None:
        items = await self.children[0].first(ctx)
        condition = self.children[1]
        item_key: str = await self.children[2].first(ctx)
        matches_key: str = await self.children[3].first(ctx)
        rest_key: str = await self.children[4].first(ctx)

        matches_list: list = []
        rest_list: list = []
        for elem in items:
            ctx.attrs[item_key] = elem
            if await condition.first(ctx):
                matches_list.append(elem)
            else:
                rest_list.append(elem)
        ctx.attrs[matches_key] = matches_list
        ctx.attrs[rest_key] = rest_list


class ToDict(Command):
    """Build a dict from items using Nu key and value expressions.

    Children: ``[items, key, value, item_key, output_key]``

    Stores the resulting dict in ``ctx.attrs[output]``.
    """

    def __init__(
        self,
        items: Arg[Iterable],
        *,
        key: Nu,
        value: Nu,
        output: StrArg = "result",
        item: StrArg = "item",
    ) -> None:
        super().__init__(items, key, value, item, output)

    async def run(self, ctx: Context) -> None:
        items = await self.children[0].first(ctx)
        key_expr = self.children[1]
        value_expr = self.children[2]
        item_key: str = await self.children[3].first(ctx)
        output_key: str = await self.children[4].first(ctx)

        result: dict = {}
        for elem in items:
            ctx.attrs[item_key] = elem
            k = await key_expr.first(ctx)
            v = await value_expr.first(ctx)
            result[k] = v
        ctx.attrs[output_key] = result
