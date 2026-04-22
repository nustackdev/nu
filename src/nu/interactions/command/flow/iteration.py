"""Collection iteration ops -- Nu-native iteration over collections.

Every predicate/transform is a Nu -- no lambdas, no holes in the tree.
Deformations see everything.

Pattern: items + Nu expression(s) + body/output + item key.
Items are set on ctx.attrs[item] each iteration so the body and
condition/transform Nus can read them via AttrRef.
"""

from __future__ import annotations

from contextlib import aclosing, closing
from typing import TYPE_CHECKING

from nu.terms import Flow


if TYPE_CHECKING:
    from collections.abc import Iterable

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
    "UniqueDo",
]


class Filter(Flow):
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

    async def arun(self, ctx: Context) -> None:
        """Execute body for each item where condition holds."""
        condition = self.children[1]
        body = self.children[2]
        item_key: str = await self.children[3].afirst(ctx)

        async with aclosing(self.children[0].aopen(ctx)) as items_gen:
            async for items in items_gen:
                for elem in items:
                    ctx.attrs[item_key] = elem
                    if await condition.afirst(ctx):
                        await body.aexecute(ctx)

    def run(self, ctx: Context) -> None:
        condition = self.children[1]
        body = self.children[2]
        item_key: str = self.children[3].first(ctx)

        with closing(self.children[0].open(ctx)) as items_gen:
            for items in items_gen:
                for elem in items:
                    ctx.attrs[item_key] = elem
                    if condition.first(ctx):
                        body.execute(ctx)


class Map(Flow):
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

    async def arun(self, ctx: Context) -> None:
        """Collect transform(item) for each item into output_key."""
        transform = self.children[1]
        item_key: str = await self.children[2].afirst(ctx)
        output_key: str = await self.children[3].afirst(ctx)

        results = []
        async with aclosing(self.children[0].aopen(ctx)) as items_gen:
            async for items in items_gen:
                for elem in items:
                    ctx.attrs[item_key] = elem
                    results.append(await transform.afirst(ctx))
        ctx.attrs[output_key] = results

    def run(self, ctx: Context) -> None:
        transform = self.children[1]
        item_key: str = self.children[2].first(ctx)
        output_key: str = self.children[3].first(ctx)

        results = []
        with closing(self.children[0].open(ctx)) as items_gen:
            for items in items_gen:
                for elem in items:
                    ctx.attrs[item_key] = elem
                    results.append(transform.first(ctx))
        ctx.attrs[output_key] = results


class TakeWhile(Flow):
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

    async def arun(self, ctx: Context) -> None:
        """Execute body while condition holds; stop on first false."""
        condition = self.children[1]
        body = self.children[2]
        item_key: str = await self.children[3].afirst(ctx)

        async with aclosing(self.children[0].aopen(ctx)) as items_gen:
            async for items in items_gen:
                for elem in items:
                    ctx.attrs[item_key] = elem
                    if not await condition.afirst(ctx):
                        return
                    await body.aexecute(ctx)

    def run(self, ctx: Context) -> None:
        condition = self.children[1]
        body = self.children[2]
        item_key: str = self.children[3].first(ctx)

        with closing(self.children[0].open(ctx)) as items_gen:
            for items in items_gen:
                for elem in items:
                    ctx.attrs[item_key] = elem
                    if not condition.first(ctx):
                        return
                    body.execute(ctx)


class UniqueDo(Flow):
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

    async def arun(self, ctx: Context) -> None:
        """Execute body for each item whose key has not been seen."""
        key_expr = self.children[1]
        body = self.children[2]
        item_key: str = await self.children[3].afirst(ctx)

        seen: set = set()
        async with aclosing(self.children[0].aopen(ctx)) as items_gen:
            async for items in items_gen:
                for elem in items:
                    ctx.attrs[item_key] = elem
                    k = await key_expr.afirst(ctx)
                    if k not in seen:
                        seen.add(k)
                        await body.aexecute(ctx)

    def run(self, ctx: Context) -> None:
        key_expr = self.children[1]
        body = self.children[2]
        item_key: str = self.children[3].first(ctx)

        seen: set = set()
        with closing(self.children[0].open(ctx)) as items_gen:
            for items in items_gen:
                for elem in items:
                    ctx.attrs[item_key] = elem
                    k = key_expr.first(ctx)
                    if k not in seen:
                        seen.add(k)
                        body.execute(ctx)


class Find(Flow):
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

    async def arun(self, ctx: Context) -> None:
        """Store the first matching element in output_key."""
        condition = self.children[1]
        item_key: str = await self.children[2].afirst(ctx)
        output_key: str = await self.children[3].afirst(ctx)

        async with aclosing(self.children[0].aopen(ctx)) as items_gen:
            async for items in items_gen:
                for elem in items:
                    ctx.attrs[item_key] = elem
                    if await condition.afirst(ctx):
                        ctx.attrs[output_key] = elem
                        return

    def run(self, ctx: Context) -> None:
        condition = self.children[1]
        item_key: str = self.children[2].first(ctx)
        output_key: str = self.children[3].first(ctx)

        with closing(self.children[0].open(ctx)) as items_gen:
            for items in items_gen:
                for elem in items:
                    ctx.attrs[item_key] = elem
                    if condition.first(ctx):
                        ctx.attrs[output_key] = elem
                        return


class FindIndex(Flow):
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

    async def arun(self, ctx: Context) -> None:
        """Store the index of the first matching element in output_key."""
        condition = self.children[1]
        item_key: str = await self.children[2].afirst(ctx)
        output_key: str = await self.children[3].afirst(ctx)

        async with aclosing(self.children[0].aopen(ctx)) as items_gen:
            async for items in items_gen:
                for i, elem in enumerate(items):
                    ctx.attrs[item_key] = elem
                    if await condition.afirst(ctx):
                        ctx.attrs[output_key] = i
                        return

    def run(self, ctx: Context) -> None:
        condition = self.children[1]
        item_key: str = self.children[2].first(ctx)
        output_key: str = self.children[3].first(ctx)

        with closing(self.children[0].open(ctx)) as items_gen:
            for items in items_gen:
                for i, elem in enumerate(items):
                    ctx.attrs[item_key] = elem
                    if condition.first(ctx):
                        ctx.attrs[output_key] = i
                        return


class GroupBy(Flow):
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

    async def arun(self, ctx: Context) -> None:
        """Group items by key, execute body once per group."""
        key_expr = self.children[1]
        body = self.children[2]
        item_key: str = await self.children[3].afirst(ctx)
        group_key: str = await self.children[4].afirst(ctx)

        groups: dict = {}
        async with aclosing(self.children[0].aopen(ctx)) as items_gen:
            async for items in items_gen:
                for elem in items:
                    ctx.attrs[item_key] = elem
                    k = await key_expr.afirst(ctx)
                    groups.setdefault(k, []).append(elem)

        for k, group_items in groups.items():
            ctx.attrs[item_key] = k
            ctx.attrs[group_key] = group_items
            await body.aexecute(ctx)

    def run(self, ctx: Context) -> None:
        key_expr = self.children[1]
        body = self.children[2]
        item_key: str = self.children[3].first(ctx)
        group_key: str = self.children[4].first(ctx)

        groups: dict = {}
        with closing(self.children[0].open(ctx)) as items_gen:
            for items in items_gen:
                for elem in items:
                    ctx.attrs[item_key] = elem
                    k = key_expr.first(ctx)
                    groups.setdefault(k, []).append(elem)

        for k, group_items in groups.items():
            ctx.attrs[item_key] = k
            ctx.attrs[group_key] = group_items
            body.execute(ctx)


class Partition(Flow):
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

    async def arun(self, ctx: Context) -> None:
        """Split items into matches/rest by condition."""
        condition = self.children[1]
        item_key: str = await self.children[2].afirst(ctx)
        matches_key: str = await self.children[3].afirst(ctx)
        rest_key: str = await self.children[4].afirst(ctx)

        matches_list: list = []
        rest_list: list = []
        async with aclosing(self.children[0].aopen(ctx)) as items_gen:
            async for items in items_gen:
                for elem in items:
                    ctx.attrs[item_key] = elem
                    if await condition.afirst(ctx):
                        matches_list.append(elem)
                    else:
                        rest_list.append(elem)
        ctx.attrs[matches_key] = matches_list
        ctx.attrs[rest_key] = rest_list

    def run(self, ctx: Context) -> None:
        condition = self.children[1]
        item_key: str = self.children[2].first(ctx)
        matches_key: str = self.children[3].first(ctx)
        rest_key: str = self.children[4].first(ctx)

        matches_list: list = []
        rest_list: list = []
        with closing(self.children[0].open(ctx)) as items_gen:
            for items in items_gen:
                for elem in items:
                    ctx.attrs[item_key] = elem
                    if condition.first(ctx):
                        matches_list.append(elem)
                    else:
                        rest_list.append(elem)
        ctx.attrs[matches_key] = matches_list
        ctx.attrs[rest_key] = rest_list


class ToDict(Flow):
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

    async def arun(self, ctx: Context) -> None:
        """Build a dict from items via key and value expressions."""
        key_expr = self.children[1]
        value_expr = self.children[2]
        item_key: str = await self.children[3].afirst(ctx)
        output_key: str = await self.children[4].afirst(ctx)

        result: dict = {}
        async with aclosing(self.children[0].aopen(ctx)) as items_gen:
            async for items in items_gen:
                for elem in items:
                    ctx.attrs[item_key] = elem
                    k = await key_expr.afirst(ctx)
                    v = await value_expr.afirst(ctx)
                    result[k] = v
        ctx.attrs[output_key] = result

    def run(self, ctx: Context) -> None:
        key_expr = self.children[1]
        value_expr = self.children[2]
        item_key: str = self.children[3].first(ctx)
        output_key: str = self.children[4].first(ctx)

        result: dict = {}
        with closing(self.children[0].open(ctx)) as items_gen:
            for items in items_gen:
                for elem in items:
                    ctx.attrs[item_key] = elem
                    k = key_expr.first(ctx)
                    v = value_expr.first(ctx)
                    result[k] = v
        ctx.attrs[output_key] = result
