"""Stream entries: drive a Program whose root yields a stream (StreamQuery).

Each opens the root value through the Runtime's ``iter`` / ``aiter``, wraps
it with ``safely_closing`` / ``safely_aclosing`` so a short-circuit (first,
partial collect) still finalizes the underlying generator, and tears the
Budget down on exit.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.lang.runtime import Budget, Context, NuRuntime, safely_aclosing, safely_closing

from ._guard import refuse_async_only


if TYPE_CHECKING:
    from nu2.engine import Program


def first(
    program: Program,
    ctx: Context | None = None,
    *,
    max_parallel: int = 1,
) -> tuple[object, Context]:
    """Return the first item of a stream-rooted Program; ``(value, ctx)``.

    Raises ``RuntimeError`` if the stream is empty.
    """
    refuse_async_only(program, "first", "afirst")
    ctx = ctx if ctx is not None else Context()
    with Budget(max_parallel, async_mode=False) as budget:
        rt = NuRuntime(program, ctx, budget=budget)
        with safely_closing(rt.iter(0)) as gen:
            for v in gen:
                return v, ctx
    msg = "first: program yielded no values"
    raise RuntimeError(msg)


def collect(
    program: Program,
    ctx: Context | None = None,
    *,
    max_parallel: int = 1,
) -> tuple[list, Context]:
    """Materialize a stream-rooted Program to a list; ``(values, ctx)``."""
    refuse_async_only(program, "collect", "acollect")
    ctx = ctx if ctx is not None else Context()
    with Budget(max_parallel, async_mode=False) as budget:
        rt = NuRuntime(program, ctx, budget=budget)
        return rt.collect(0), ctx


async def afirst(
    program: Program,
    ctx: Context | None = None,
    *,
    max_parallel: int = 1,
) -> tuple[object, Context]:
    """Async sibling of ``first``."""
    ctx = ctx if ctx is not None else Context()
    with Budget(max_parallel, async_mode=True) as budget:
        rt = NuRuntime(program, ctx, budget=budget)
        async with safely_aclosing(await rt.aiter(0)) as agen:
            async for v in agen:
                return v, ctx
    msg = "afirst: program yielded no values"
    raise RuntimeError(msg)


async def alast(
    program: Program,
    ctx: Context | None = None,
    *,
    max_parallel: int = 1,
) -> tuple[object, Context]:
    """Drain a stream-rooted Program and return the last item; ``(value, ctx)``.

    Raises ``RuntimeError`` if the stream is empty.
    """
    ctx = ctx if ctx is not None else Context()
    found = False
    last: object = None
    with Budget(max_parallel, async_mode=True) as budget:
        rt = NuRuntime(program, ctx, budget=budget)
        async with safely_aclosing(await rt.aiter(0)) as agen:
            async for v in agen:
                last = v
                found = True
    if not found:
        msg = "alast: program yielded no values"
        raise RuntimeError(msg)
    return last, ctx


async def acollect(
    program: Program,
    ctx: Context | None = None,
    *,
    max_parallel: int = 1,
) -> tuple[list, Context]:
    """Async sibling of ``collect``."""
    ctx = ctx if ctx is not None else Context()
    with Budget(max_parallel, async_mode=True) as budget:
        rt = NuRuntime(program, ctx, budget=budget)
        return await rt.acollect(0), ctx
