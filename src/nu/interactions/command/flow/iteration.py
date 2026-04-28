"""Collection iteration ops -- Filter, Map, TakeWhile, UniqueDo, Find,
FindIndex, GroupBy, Partition, ToDict.

Stream-shaped variants (Filter, Map, TakeWhile, UniqueDo) are
``StreamQuery`` -- they yield items pulled from a stream child, gated by
a Nu predicate / transform child. Reduction-shaped variants (Find,
FindIndex, GroupBy, Partition, ToDict) are ``ScalarQuery`` returning a
single scalar value (the match, the dict, the partition tuple).

Per-item Nu predicates / transforms are evaluated against ``ctx.attrs``
keyed by an item key (string), so the predicate body can read the
current element via ``AttrRef``. The item-key plumbing keeps the legacy
authoring style; new-core only sees a stream pull and a scalar lookup.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.query import Reduction, ScalarQuery, StreamQuery  # noqa: F401
from nu.terms.types import Mode


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator, Iterable

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


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


def _iterate_sync(items_q: Nu, ctx: Any) -> Generator[Any, None, None]:  # noqa: ANN401
    """Open the items stream and yield each individual element.

    Legacy items children yield batches (iterables); flatten them.
    """
    from contextlib import closing

    with closing(items_q.open(ctx)) as gen:
        for batch in gen:
            if hasattr(batch, "__iter__") and not isinstance(batch, (str, bytes)):
                yield from batch
            else:
                yield batch


async def _iterate_async(items_q: Nu, ctx: Any) -> AsyncGenerator[Any, None]:  # noqa: ANN401
    from contextlib import aclosing

    async with aclosing(items_q.aopen(ctx)) as gen:
        async for batch in gen:
            if hasattr(batch, "__iter__") and not isinstance(batch, (str, bytes)):
                for elem in batch:
                    yield elem
            else:
                yield batch


# --- Stream-shaped: Filter, Map, TakeWhile, UniqueDo ------------------------


class Filter(StreamQuery):
    """Yield items where the condition is truthy.

    Children: ``[items, condition, item_key]``
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

    def open(self, ctx: Any) -> Generator[Any, None, None]:  # noqa: ANN401
        from nu import runtime

        condition = self._children[1]
        item_key: str = runtime.first(self._children[2], ctx)
        for elem in _iterate_sync(self._children[0], ctx):
            ctx.attrs[item_key] = elem
            if runtime.first(condition, ctx):
                yield elem

    async def aopen(self, ctx: Any) -> AsyncGenerator[Any, None]:  # noqa: ANN401
        from nu import runtime

        condition = self._children[1]
        item_key: str = await runtime.afirst(self._children[2], ctx)
        async for elem in _iterate_async(self._children[0], ctx):
            ctx.attrs[item_key] = elem
            if await runtime.afirst(condition, ctx):
                yield elem


class Map(StreamQuery):
    """Yield ``transform(item)`` for each item.

    Children: ``[items, transform, item_key]``
    """

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(
        self,
        items: Arg[Iterable],
        *,
        transform: Nu,
        item: StrArg = "item",
    ) -> None:
        super().__init__(items, transform, item)

    def open(self, ctx: Any) -> Generator[Any, None, None]:  # noqa: ANN401
        from nu import runtime

        transform = self._children[1]
        item_key: str = runtime.first(self._children[2], ctx)
        for elem in _iterate_sync(self._children[0], ctx):
            ctx.attrs[item_key] = elem
            yield runtime.first(transform, ctx)

    async def aopen(self, ctx: Any) -> AsyncGenerator[Any, None]:  # noqa: ANN401
        from nu import runtime

        transform = self._children[1]
        item_key: str = await runtime.afirst(self._children[2], ctx)
        async for elem in _iterate_async(self._children[0], ctx):
            ctx.attrs[item_key] = elem
            yield await runtime.afirst(transform, ctx)


class TakeWhile(StreamQuery):
    """Yield items while condition holds; stop on first false.

    Children: ``[items, condition, item_key]``
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

    def open(self, ctx: Any) -> Generator[Any, None, None]:  # noqa: ANN401
        from nu import runtime

        condition = self._children[1]
        item_key: str = runtime.first(self._children[2], ctx)
        for elem in _iterate_sync(self._children[0], ctx):
            ctx.attrs[item_key] = elem
            if not runtime.first(condition, ctx):
                return
            yield elem

    async def aopen(self, ctx: Any) -> AsyncGenerator[Any, None]:  # noqa: ANN401
        from nu import runtime

        condition = self._children[1]
        item_key: str = await runtime.afirst(self._children[2], ctx)
        async for elem in _iterate_async(self._children[0], ctx):
            ctx.attrs[item_key] = elem
            if not await runtime.afirst(condition, ctx):
                return
            yield elem


class UniqueDo(StreamQuery):
    """Yield items whose key value has not been seen yet.

    Children: ``[items, key, item_key]``
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

    def open(self, ctx: Any) -> Generator[Any, None, None]:  # noqa: ANN401
        from nu import runtime

        key_expr = self._children[1]
        item_key: str = runtime.first(self._children[2], ctx)
        seen: set = set()
        for elem in _iterate_sync(self._children[0], ctx):
            ctx.attrs[item_key] = elem
            k = runtime.first(key_expr, ctx)
            if k not in seen:
                seen.add(k)
                yield elem

    async def aopen(self, ctx: Any) -> AsyncGenerator[Any, None]:  # noqa: ANN401
        from nu import runtime

        key_expr = self._children[1]
        item_key: str = await runtime.afirst(self._children[2], ctx)
        seen: set = set()
        async for elem in _iterate_async(self._children[0], ctx):
            ctx.attrs[item_key] = elem
            k = await runtime.afirst(key_expr, ctx)
            if k not in seen:
                seen.add(k)
                yield elem


# --- Scalar-shaped: Find, FindIndex, GroupBy, Partition, ToDict --------------


class Find(Reduction):
    """Return the first item where condition is truthy. ``None`` if none.

    Children: ``[items, condition, item_key]``
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
    """Return the index of the first item where condition is truthy.

    Children: ``[items, condition, item_key]``. ``-1`` if none.
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
    """Return ``{key: [items]}`` grouped by Nu key.

    Children: ``[items, key, item_key]``
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
    """Return ``(matches, rest)`` split by Nu condition.

    Children: ``[items, condition, item_key]``
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
    """Return a dict built from key/value Nu expressions over each item.

    Children: ``[items, key, value, item_key]``
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
