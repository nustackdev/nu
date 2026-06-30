"""SortBy - keyed sort of a stream/iterable.

Each item is bound to `ctx.attrs[item_key]` and the `key` Nu is evaluated
per item to produce the sort key. Returns a Python list.
"""

from __future__ import annotations

from contextlib import aclosing, closing
from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.query import Reduction
from nu.terms.types import Mode


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator

    from nu.terms import Arg, BoolArg, Nu, StrArg


__all__ = ["SortBy"]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class SortBy(Reduction):
    """Sort items by a per-item Nu key.

    Children: `[items, key, reverse, item_key]`.
    """

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(
        self,
        items: Arg,
        *,
        key: Nu,
        reverse: BoolArg = False,
        item: StrArg = "item",
    ) -> None:
        super().__init__(items, key, reverse, item)

    def eval(self, ctx: Any) -> list[Any]:  # noqa: ANN401, D102
        from nu import runtime

        key_expr = self._children[1]
        reverse: bool = bool(runtime.first(self._children[2], ctx))
        item_key: str = runtime.first(self._children[3], ctx)
        rows: list[tuple[Any, Any]] = []
        for elem in self._iter_sync(ctx):
            ctx.attrs[item_key] = elem
            rows.append((runtime.first(key_expr, ctx), elem))
        rows.sort(key=lambda kv: kv[0], reverse=reverse)
        return [v for _, v in rows]

    async def aeval(self, ctx: Any) -> list[Any]:  # noqa: ANN401, D102
        from nu import runtime

        key_expr = self._children[1]
        reverse: bool = bool(await runtime.afirst(self._children[2], ctx))
        item_key: str = await runtime.afirst(self._children[3], ctx)
        rows: list[tuple[Any, Any]] = []
        async for elem in self._iter_async(ctx):
            ctx.attrs[item_key] = elem
            rows.append((await runtime.afirst(key_expr, ctx), elem))
        rows.sort(key=lambda kv: kv[0], reverse=reverse)
        return [v for _, v in rows]

    # Non-unpacking iterators: each elem yielded by the source is one item.
    # The shared `_iterate_async` in iter_reduce.py auto-flattens any iterable
    # batch, which breaks for streams of dicts (it yields the dict's keys).

    def _iter_sync(self, ctx: Any) -> Generator[Any, None, None]:  # noqa: ANN401
        items_q = self._children[0]
        if hasattr(items_q, "open"):
            with closing(items_q.open(ctx)) as gen:
                yield from gen
            return
        from nu import runtime

        value = runtime.first(items_q, ctx)
        yield from value

    async def _iter_async(self, ctx: Any) -> AsyncGenerator[Any, None]:  # noqa: ANN401
        items_q = self._children[0]
        if hasattr(items_q, "aopen"):
            async with aclosing(items_q.aopen(ctx)) as gen:
                async for elem in gen:
                    yield elem
            return
        from nu import runtime

        value = await runtime.afirst(items_q, ctx)
        for v in value:
            yield v
