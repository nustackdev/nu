"""Stream-driven scalar reductions - Find, FindIndex, GroupBy, Partition, ToDict.

Reduction kinds (ScalarQuery whose child is a stream) that consume a
stream child and return a single scalar (the match, the dict, the
partition tuple).

Per-item Nu predicates / transforms are evaluated against `ctx.attrs`
keyed by an item key (string) - the predicate body reads the current
element via `AttrRef`.
"""

from __future__ import annotations

from contextlib import aclosing, closing
from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.query import Reduction
from nu.terms.types import Mode


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator, Iterable

    from nu.terms import Arg, Nu, StrArg


__all__ = [
    "Find",
    "FindIndex",
    "GroupBy",
    "Partition",
    "ToDict",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


def _iterate_sync(items_q: Any, ctx: Any) -> Generator[Any, None, None]:  # noqa: ANN401
    if hasattr(items_q, "open"):
        with closing(items_q.open(ctx)) as gen:
            for batch in gen:
                if hasattr(batch, "__iter__") and not isinstance(batch, (str, bytes)):
                    yield from batch
                else:
                    yield batch
        return
    from nu import runtime

    value = runtime.first(items_q, ctx)
    yield from value


async def _iterate_async(items_q: Any, ctx: Any) -> AsyncGenerator[Any, None]:  # noqa: ANN401
    if hasattr(items_q, "aopen"):
        async with aclosing(items_q.aopen(ctx)) as gen:
            async for batch in gen:
                if hasattr(batch, "__iter__") and not isinstance(batch, (str, bytes)):
                    for elem in batch:
                        yield elem
                else:
                    yield batch
        return
    from nu import runtime

    value = await runtime.afirst(items_q, ctx)
    for v in value:
        yield v


class Find(Reduction):
    """First item where condition is truthy, or `None`.

    Children: `[items, condition, item_key]`
    """

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(
        self,
        items: Arg[Iterable],
        *,
        condition: Nu,
        item: StrArg = "item",
    ) -> None:
        super().__init__(items, condition, item)

    def eval(self, ctx: Any) -> Any:  # noqa: ANN401
        from nu import runtime

        condition = self._children[1]
        item_key: str = runtime.first(self._children[2], ctx)
        for elem in _iterate_sync(self._children[0], ctx):
            ctx.attrs[item_key] = elem
            if runtime.first(condition, ctx):
                return elem
        return None

    async def aeval(self, ctx: Any) -> Any:  # noqa: ANN401
        from nu import runtime

        condition = self._children[1]
        item_key: str = await runtime.afirst(self._children[2], ctx)
        async for elem in _iterate_async(self._children[0], ctx):
            ctx.attrs[item_key] = elem
            if await runtime.afirst(condition, ctx):
                return elem
        return None


class FindIndex(Reduction):
    """Index of first item where condition is truthy. `-1` if none.

    Children: `[items, condition, item_key]`
    """

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(
        self,
        items: Arg[Iterable],
        *,
        condition: Nu,
        item: StrArg = "item",
    ) -> None:
        super().__init__(items, condition, item)

    def eval(self, ctx: Any) -> int:
        from nu import runtime

        condition = self._children[1]
        item_key: str = runtime.first(self._children[2], ctx)
        for i, elem in enumerate(_iterate_sync(self._children[0], ctx)):
            ctx.attrs[item_key] = elem
            if runtime.first(condition, ctx):
                return i
        return -1

    async def aeval(self, ctx: Any) -> int:
        from nu import runtime

        condition = self._children[1]
        item_key: str = await runtime.afirst(self._children[2], ctx)
        i = 0
        async for elem in _iterate_async(self._children[0], ctx):
            ctx.attrs[item_key] = elem
            if await runtime.afirst(condition, ctx):
                return i
            i += 1
        return -1


class GroupBy(Reduction):
    """`{key: [items]}` grouped by Nu key.

    Children: `[items, key, item_key]`
    """

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(
        self,
        items: Arg[Iterable],
        *,
        key: Nu,
        item: StrArg = "item",
    ) -> None:
        super().__init__(items, key, item)

    def eval(self, ctx: Any) -> dict:
        from nu import runtime

        key_expr = self._children[1]
        item_key: str = runtime.first(self._children[2], ctx)
        groups: dict = {}
        for elem in _iterate_sync(self._children[0], ctx):
            ctx.attrs[item_key] = elem
            k = runtime.first(key_expr, ctx)
            groups.setdefault(k, []).append(elem)
        return groups

    async def aeval(self, ctx: Any) -> dict:
        from nu import runtime

        key_expr = self._children[1]
        item_key: str = await runtime.afirst(self._children[2], ctx)
        groups: dict = {}
        async for elem in _iterate_async(self._children[0], ctx):
            ctx.attrs[item_key] = elem
            k = await runtime.afirst(key_expr, ctx)
            groups.setdefault(k, []).append(elem)
        return groups


class Partition(Reduction):
    """`(matches, rest)` split by Nu condition.

    Children: `[items, condition, item_key]`
    """

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(
        self,
        items: Arg[Iterable],
        *,
        condition: Nu,
        item: StrArg = "item",
    ) -> None:
        super().__init__(items, condition, item)

    def eval(self, ctx: Any) -> tuple[list, list]:
        from nu import runtime

        condition = self._children[1]
        item_key: str = runtime.first(self._children[2], ctx)
        matches: list = []
        rest: list = []
        for elem in _iterate_sync(self._children[0], ctx):
            ctx.attrs[item_key] = elem
            if runtime.first(condition, ctx):
                matches.append(elem)
            else:
                rest.append(elem)
        return matches, rest

    async def aeval(self, ctx: Any) -> tuple[list, list]:
        from nu import runtime

        condition = self._children[1]
        item_key: str = await runtime.afirst(self._children[2], ctx)
        matches: list = []
        rest: list = []
        async for elem in _iterate_async(self._children[0], ctx):
            ctx.attrs[item_key] = elem
            if await runtime.afirst(condition, ctx):
                matches.append(elem)
            else:
                rest.append(elem)
        return matches, rest


class ToDict(Reduction):
    """Dict built from key/value Nu expressions over each item.

    Children: `[items, key, value, item_key]`
    """

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(
        self,
        items: Arg[Iterable],
        *,
        key: Nu,
        value: Nu,
        item: StrArg = "item",
    ) -> None:
        super().__init__(items, key, value, item)

    def eval(self, ctx: Any) -> dict:
        from nu import runtime

        key_expr = self._children[1]
        value_expr = self._children[2]
        item_key: str = runtime.first(self._children[3], ctx)
        result: dict = {}
        for elem in _iterate_sync(self._children[0], ctx):
            ctx.attrs[item_key] = elem
            k = runtime.first(key_expr, ctx)
            v = runtime.first(value_expr, ctx)
            result[k] = v
        return result

    async def aeval(self, ctx: Any) -> dict:
        from nu import runtime

        key_expr = self._children[1]
        value_expr = self._children[2]
        item_key: str = await runtime.afirst(self._children[3], ctx)
        result: dict = {}
        async for elem in _iterate_async(self._children[0], ctx):
            ctx.attrs[item_key] = elem
            k = await runtime.afirst(key_expr, ctx)
            v = await runtime.afirst(value_expr, ctx)
            result[k] = v
        return result
