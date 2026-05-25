"""Value entries: drive a Program whose root yields a single value."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.lang.runtime import Budget, Context, NuRuntime, into_loop

from ._guard import refuse_async_only


if TYPE_CHECKING:
    from nu2.engine import Program


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
        rt = NuRuntime(program, ctx, budget=budget)
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
        rt = NuRuntime(program, ctx, budget=budget)
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
