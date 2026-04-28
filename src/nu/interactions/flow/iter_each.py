"""ForEach - iterate items and bind each to a context attr.

`nu.terms.flow.ForEachDo` runs a body per item but doesn't bind the
item to `ctx.attrs` - the body has nothing to read. This `ForEach`
adds the legacy item-binding so the body can read each element via
`AttrRef(item_key)`.

Children: `[items, body, item_key]`. Body lives at slot 1.
"""

from __future__ import annotations

from contextlib import aclosing, closing
from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.flow import Control
from nu.terms.types import Mode


if TYPE_CHECKING:
    from collections.abc import Iterable

    from nu.terms import Arg, Nu, StrArg


__all__ = ["ForEach"]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class ForEach(Control):
    """Run body for each item in `items`. Binds each element to `ctx.attrs[item_key]`.

    `items` may be a ScalarQuery whose value is iterable (list, tuple,
    range, dict, ...) or a StreamQuery. Body is a Command at slot 1.
    """

    body_slots: ClassVar[tuple[int, ...]] = (1,)
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(
        self,
        items: Arg[Iterable],
        body: Nu,
        *,
        item: StrArg = "item",
    ) -> None:
        super().__init__(items, body, item)

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        items_q = self._children[0]
        body = self._children[1]
        item_key: str = runtime.first(self._children[2], ctx)
        for elem in _iterate_sync(items_q, ctx):
            ctx.attrs[item_key] = elem
            runtime.execute(body, ctx)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        items_q = self._children[0]
        body = self._children[1]
        item_key: str = await runtime.afirst(self._children[2], ctx)
        async for elem in _iterate_async(items_q, ctx):
            ctx.attrs[item_key] = elem
            await runtime.aexecute(body, ctx)


def _iterate_sync(items_q: Any, ctx: Any):  # noqa: ANN401, ANN202
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


async def _iterate_async(items_q: Any, ctx: Any):  # noqa: ANN401, ANN202
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
