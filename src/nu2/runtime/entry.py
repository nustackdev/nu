"""Top-level entry points: construct a Runtime, dispatch to the root, return.

Each entry owns a fresh ``Budget`` for the call, sized by ``max_parallel``,
and closes it on exit. The Runtime sees the Budget through construction; no
global state.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.context import Context
from nu2.runtime.budget import Budget
from nu2.runtime.driver import Runtime
from nu2.runtime.loop import into_loop


if TYPE_CHECKING:
    from nu2.attribute import Program

__all__ = ["aeval", "eval", "eval_in_loop"]


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
    """
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
