"""Stream transforms - Filter, Map, StreamTake, TakeWhile, UniqueDo.

StreamQuery kinds that pull items from a stream child and yield them
gated/transformed by a per-item Nu predicate or transform child.

Per-item Nu children read the current element via `ctx.attrs[item_key]`.
"""

from __future__ import annotations

import inspect
from collections.abc import Mapping
from contextlib import aclosing, closing
from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.query import StreamQuery
from nu.terms.types import Mode


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable, Generator, Iterable

    from nu.terms import Arg, IntArg, Nu, StrArg


__all__ = [
    "Filter",
    "FilterFn",
    "FlatMapFn",
    "Map",
    "MapFn",
    "StreamTake",
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
                if hasattr(batch, "__iter__") and not isinstance(batch, (str, bytes, Mapping)):
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
                if hasattr(batch, "__iter__") and not isinstance(batch, (str, bytes, Mapping)):
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

    def open(self, ctx: Any) -> Generator[Any, None, None]:  # noqa: ANN401, D102
        from nu import runtime

        condition = self._children[1]
        item_key: str = runtime.first(self._children[2], ctx)
        for elem in _iterate_sync(self._children[0], ctx):
            ctx.attrs[item_key] = elem
            if runtime.first(condition, ctx):
                yield elem

    async def aopen(self, ctx: Any) -> AsyncGenerator[Any, None]:  # noqa: ANN401, D102
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

    def open(self, ctx: Any) -> Generator[Any, None, None]:  # noqa: ANN401, D102
        from nu import runtime

        transform = self._children[1]
        item_key: str = runtime.first(self._children[2], ctx)
        for elem in _iterate_sync(self._children[0], ctx):
            ctx.attrs[item_key] = elem
            yield runtime.first(transform, ctx)

    async def aopen(self, ctx: Any) -> AsyncGenerator[Any, None]:  # noqa: ANN401, D102
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

    def open(self, ctx: Any) -> Generator[Any, None, None]:  # noqa: ANN401, D102
        from nu import runtime

        condition = self._children[1]
        item_key: str = runtime.first(self._children[2], ctx)
        for elem in _iterate_sync(self._children[0], ctx):
            ctx.attrs[item_key] = elem
            if not runtime.first(condition, ctx):
                return
            yield elem

    async def aopen(self, ctx: Any) -> AsyncGenerator[Any, None]:  # noqa: ANN401, D102
        from nu import runtime

        condition = self._children[1]
        item_key: str = await runtime.afirst(self._children[2], ctx)
        async for elem in _iterate_async(self._children[0], ctx):
            ctx.attrs[item_key] = elem
            if not await runtime.afirst(condition, ctx):
                return
            yield elem


class StreamTake(StreamQuery):
    """Yield the first `n` items, then stop pulling.

    Count-based twin of `TakeWhile`: consumes a stream and yields its
    prefix of length `n`, stopping as soon as `n` items are out. It pulls
    at most `n` items from its child, so the upstream is never drained
    past the cap. `n <= 0` yields nothing; a stream shorter than `n`
    yields all of it.

    Children: `[items, n]`
    """

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, items: Arg[Iterable], n: IntArg) -> None:
        super().__init__(items, n)

    def open(self, ctx: Any) -> Generator[Any, None, None]:  # noqa: ANN401, D102
        from nu import runtime

        n = int(runtime.first(self._children[1], ctx))
        if n <= 0:
            return
        count = 0
        for elem in _iterate_sync(self._children[0], ctx):
            yield elem
            count += 1
            if count >= n:
                return

    async def aopen(self, ctx: Any) -> AsyncGenerator[Any, None]:  # noqa: ANN401, D102
        from nu import runtime

        n = int(await runtime.afirst(self._children[1], ctx))
        if n <= 0:
            return
        count = 0
        async for elem in _iterate_async(self._children[0], ctx):
            yield elem
            count += 1
            if count >= n:
                return


def _fn_support(fn: Callable[..., Any]) -> frozenset[Mode]:
    target = fn
    while hasattr(target, "__wrapped__"):
        target = target.__wrapped__
    if inspect.iscoroutinefunction(target) or inspect.isasyncgenfunction(target):
        return frozenset({Mode.ASYNC})
    return _BOTH


class FilterFn(StreamQuery):
    """Yield items where `predicate(item)` is truthy.

    Variant of `Filter` that takes a python callable instead of a Nu
    subtree. The callable receives the current element positionally and
    returns a bool. `async def` predicates narrow support to ASYNC-only.

    Children: `[items]`. The callable is held as `self._fn`.
    """

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(
        self,
        items: Arg[Iterable],
        predicate: Callable[[Any], Any],
    ) -> None:
        super().__init__(items)
        self._fn = predicate
        self.support = _fn_support(predicate)  # type: ignore[misc]

    def open(self, ctx: Any) -> Generator[Any, None, None]:  # noqa: ANN401, D102
        fn = self._fn
        for elem in _iterate_sync(self._children[0], ctx):
            if fn(elem):
                yield elem

    async def aopen(self, ctx: Any) -> AsyncGenerator[Any, None]:  # noqa: ANN401, D102
        fn = self._fn
        async for elem in _iterate_async(self._children[0], ctx):
            result = fn(elem)
            if inspect.isawaitable(result):
                result = await result
            if result:
                yield elem

    def __repr__(self) -> str:
        name = getattr(self._fn, "__qualname__", None) or getattr(
            self._fn, "__name__", repr(self._fn)
        )
        return f"FilterFn({self._children[0]!r}, {name})"


class MapFn(StreamQuery):
    """Yield `transform(item)` for each item.

    Variant of `Map` that takes a python callable instead of a Nu subtree.
    The callable receives the current element positionally and returns the
    transformed value. `async def` transforms narrow support to ASYNC-only.

    Children: `[items]`. The callable is held as `self._fn`.
    """

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(
        self,
        items: Arg[Iterable],
        transform: Callable[[Any], Any],
    ) -> None:
        super().__init__(items)
        self._fn = transform
        self.support = _fn_support(transform)  # type: ignore[misc]

    def open(self, ctx: Any) -> Generator[Any, None, None]:  # noqa: ANN401, D102
        fn = self._fn
        for elem in _iterate_sync(self._children[0], ctx):
            yield fn(elem)

    async def aopen(self, ctx: Any) -> AsyncGenerator[Any, None]:  # noqa: ANN401, D102
        fn = self._fn
        async for elem in _iterate_async(self._children[0], ctx):
            result = fn(elem)
            if inspect.isawaitable(result):
                result = await result
            yield result

    def __repr__(self) -> str:
        name = getattr(self._fn, "__qualname__", None) or getattr(
            self._fn, "__name__", repr(self._fn)
        )
        return f"MapFn({self._children[0]!r}, {name})"


class FlatMapFn(StreamQuery):
    """Yield items from `transform(item)` for each item, flat-concatenated.

    Variant of `MapFn` whose callable returns a stream-or-iterable per
    element. Each per-element result is drained and its items are
    yielded into one flat output stream.

    `transform(elem)` may return:
      - a Nu Query (StreamQuery or scalar): runtime drains its stream
        (or iterates its scalar value).
      - a Python iterable (list, tuple, generator): runtime yields from it.
      - an awaitable that resolves to either of the above (async path only).

    `async def` transforms narrow support to ASYNC-only.

    Children: `[items]`. The callable is held as `self._fn`.

    Snapshot caveat: the auto-wrapper cannot see across sibling subtrees.
    When the source is a lazy ref (e.g. `dict_ref.values`) and the body
    reads fields off elements via separate lazy refs, wrap the whole
    `FlatMapFn(...)` term in `nv.Snapshot(..., scope=...)` manually,
    or the source iteration and per-element reads will land in
    different snapshot generations.
    """

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(
        self,
        items: Arg[Iterable],
        transform: Callable[[Any], Any],
    ) -> None:
        super().__init__(items)
        self._fn = transform
        self.support = _fn_support(transform)  # type: ignore[misc]

    def open(self, ctx: Any) -> Generator[Any, None, None]:  # noqa: ANN401, D102
        fn = self._fn
        for elem in _iterate_sync(self._children[0], ctx):
            result = fn(elem)
            if hasattr(result, "open") or hasattr(result, "aopen"):
                yield from _iterate_sync(result, ctx)
            elif isinstance(result, (str, bytes)):
                yield result
            else:
                yield from result

    async def aopen(self, ctx: Any) -> AsyncGenerator[Any, None]:  # noqa: ANN401, D102
        fn = self._fn
        async for elem in _iterate_async(self._children[0], ctx):
            result = fn(elem)
            if inspect.isawaitable(result):
                result = await result
            if hasattr(result, "open") or hasattr(result, "aopen"):
                async for v in _iterate_async(result, ctx):
                    yield v
            elif isinstance(result, (str, bytes)):
                yield result
            else:
                for v in result:
                    yield v

    def __repr__(self) -> str:
        name = getattr(self._fn, "__qualname__", None) or getattr(
            self._fn, "__name__", repr(self._fn)
        )
        return f"FlatMapFn({self._children[0]!r}, {name})"


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

    def open(self, ctx: Any) -> Generator[Any, None, None]:  # noqa: ANN401, D102
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

    async def aopen(self, ctx: Any) -> AsyncGenerator[Any, None]:  # noqa: ANN401, D102
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
