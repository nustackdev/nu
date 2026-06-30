"""Drive entries: run a compiled Program through the Runtime.

Two families, by what the root yields:

- value root: ``eval``, ``aeval``, ``eval_in_loop`` -- return ``(value, ctx)``.
- stream root: ``first``, ``collect``, ``afirst``, ``alast``, ``acollect``
  -- iterate the root and return either a single item or a list, with the
  Context after execution.

Each opens a fresh ``Budget`` sized by ``max_parallel`` and closes it on
exit. Sync entries refuse a Program with an async-only subtree -- callers
must use the async sibling, or ``eval_in_loop`` as the deliberate bridge.
Stream entries wrap iteration in ``safely_(a)closing`` so a short-circuit
(``first``, partial ``collect``) still finalizes the underlying generator.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang.runtime import Budget, Context, Runtime, into_loop, safely_aclosing, safely_closing

from ._guard import refuse_async_only


if TYPE_CHECKING:
    from nu.engine import Program


# --- value root -----------------------------------------------------------


def eval(
    program: Program,
    ctx: Context | None = None,
    *,
    max_parallel: int = 1,
) -> tuple[object, Context]:
    """Drive a Program synchronously; return ``(value, ctx)``.

    Args:
        program: a compiled Program.
        ctx: the Context to drive against; a fresh one if omitted.
        max_parallel: tree-wide concurrency gate. ``1`` is sequential.

    Returns:
        The value the root produced (None for effect-only programs) and the
        Context after execution.

    Raises:
        RuntimeError: the program subtree contains an async-only atom; use
            ``aeval`` instead.
    """
    refuse_async_only(program, "eval", "aeval")
    ctx = ctx if ctx is not None else Context()
    with Budget(max_parallel, async_mode=False) as budget:
        rt = Runtime(program, ctx, budget=budget)
        return rt.eval(), ctx


async def aeval(
    program: Program,
    ctx: Context | None = None,
    *,
    max_parallel: int = 1,
) -> tuple[object, Context]:
    """Drive a Program asynchronously; return ``(value, ctx)``."""
    ctx = ctx if ctx is not None else Context()
    with Budget(max_parallel, async_mode=True) as budget:
        rt = Runtime(program, ctx, budget=budget)
        return await rt.aeval(), ctx


def eval_in_loop(
    program: Program,
    ctx: Context | None = None,
    *,
    max_parallel: int = 1,
) -> tuple[object, Context]:
    """Drive an async-only Program from sync code by spinning a loop.

    Convenience for the rare top-level sync caller whose Program contains an
    async-only atom. Most callers should use ``aeval`` directly.
    """
    return into_loop(aeval(program, ctx, max_parallel=max_parallel))


# --- stream root ----------------------------------------------------------


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
        rt = Runtime(program, ctx, budget=budget)
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
        rt = Runtime(program, ctx, budget=budget)
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
        rt = Runtime(program, ctx, budget=budget)
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
        rt = Runtime(program, ctx, budget=budget)
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
        rt = Runtime(program, ctx, budget=budget)
        return await rt.acollect(0), ctx
