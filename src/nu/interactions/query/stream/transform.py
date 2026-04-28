"""Stream transforms - Filter, Map, TakeWhile, UniqueDo.

StreamQuery kinds that pull items from a stream child and yield them
gated/transformed by a per-item Nu predicate or transform child.

Per-item Nu children read the current element via `ctx.attrs[item_key]`.
"""

from __future__ import annotations

from contextlib import aclosing, closing
from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.query import StreamQuery
from nu.terms.types import Mode


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator, Iterable

    from nu.terms import Arg, Nu, StrArg


__all__ = [
    "Filter",
    "Map",
    "TakeWhile",
    "UniqueDo",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


def _iterate_sync(items_q: Any, ctx: Any) -> Generator[Any, None, None]:  # noqa: ANN401
    """Yield each item from a stream-or-scalar child.

    Stream children (have `.open`) are drained; batches are flattened.
    Scalar children are evaluated once and their value is iterated.
    """
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


class Filter(StreamQuery):
    """Yield items where the condition is truthy.

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
    """Yield `transform(item)` for each item.

    Children: `[items, transform, item_key]`
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
