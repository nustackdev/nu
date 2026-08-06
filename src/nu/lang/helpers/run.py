"""All-in-one entries: compile, validate, drive in one call.

Take a Term, compile it against the Nu schema, validate against the Nu
law set, then drive. Three phases in one call, what app code usually
wants. The standalone pieces stay available via ``nu.lang`` for callers
that want a Program in hand (e.g. for static inspection).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, cast

from nu.lang.runtime import into_loop

from .drive import aeval, eval


if TYPE_CHECKING:
    from nu.lang.nu import Nu
    from nu.lang.runtime import Context

V = TypeVar("V")


def run(  # TypeVar matches the kind-chain V_co convention
    term: Nu[V],
    ctx: Context | None = None,
    *,
    max_parallel: int = 1,
) -> tuple[V, Context]:
    """Compile a Term, validate it, evaluate it; return ``(value, ctx)``.

    Args:
        term: a Nu Term (the description).
        ctx: the Context to drive against; a fresh one if omitted.
        max_parallel: tree-wide concurrency gate. ``1`` is sequential.

    Returns:
        The value the root produced (None for effect-only programs) and the
        Context after execution.

    Raises:
        ValueError: the Term fails Nu law validation.
        RuntimeError: the Program subtree contains an async-only atom; use
            ``arun`` instead.
    """
    from nu.lang import LAWS, compile, validate

    program = compile(term)
    validate(program, *LAWS)
    value, ctx = eval(program, ctx, max_parallel=max_parallel)
    # runtime thunks are object-typed; V is recovered from the typed entry point
    return cast("V", value), ctx


async def arun(  # TypeVar matches the kind-chain V_co convention
    term: Nu[V],
    ctx: Context | None = None,
    *,
    max_parallel: int = 1,
) -> tuple[V, Context]:
    """Async sibling of ``run``: compile, validate, then ``aeval``."""
    from nu.lang import LAWS, compile, validate

    program = compile(term)
    validate(program, *LAWS)
    value, ctx = await aeval(program, ctx, max_parallel=max_parallel)
    # runtime thunks are object-typed; V is recovered from the typed entry point
    return cast("V", value), ctx


def run_in_loop(  # TypeVar matches the kind-chain V_co convention
    term: Nu[V],
    ctx: Context | None = None,
    *,
    max_parallel: int = 1,
) -> tuple[V, Context]:
    """Compile, validate, then drive on a fresh loop from sync code.

    For the rare top-level sync caller whose Term compiles to an async-only
    Program: spins a loop via ``asyncio.run`` and drives the async path so
    the caller doesn't have to write an ``async def``. Most callers should
    use ``arun`` directly.
    """
    return into_loop(arun(term, ctx, max_parallel=max_parallel))
