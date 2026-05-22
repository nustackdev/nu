"""Term-level convenience entries: compile, validate, evaluate in one call.

The all-in-one entry: take a Term, compile it against the Nu schema,
validate against the Nu law set, then drive. Three phases in one call -
what app code usually wants. The compile/validate pieces are still
available standalone via ``nu2.lang`` for callers that want a Program in
hand (e.g. for static inspection).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.engine.evaluation.loop import into_loop
from nu2.lang.entry.value import aeval, eval


if TYPE_CHECKING:
    from nu2.engine.structure import Term
    from nu2.lang.evaluation.context import Context


def run(
    term: Term,
    ctx: Context | None = None,
    *,
    max_parallel: int = 1,
) -> tuple[object, Context]:
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
    from nu2.lang import LAWS, compile, validate

    # Compilation phase
    program = compile(term)

    # Validation phase
    validate(program, *LAWS)

    # Evaluation phase
    result = eval(program, ctx, max_parallel=max_parallel)

    return result


async def arun(
    term: Term,
    ctx: Context | None = None,
    *,
    max_parallel: int = 1,
) -> tuple[object, Context]:
    """Async sibling of ``run``: compile, validate, then ``aeval``."""
    from nu2.lang import LAWS, compile, validate

    # Compilation phase
    program = compile(term)

    # Validation phase
    validate(program, *LAWS)

    # Evaluation phase
    result = await aeval(program, ctx, max_parallel=max_parallel)

    return result


def run_in_loop(
    term: Term,
    ctx: Context | None = None,
    *,
    max_parallel: int = 1,
) -> tuple[object, Context]:
    """Compile, validate, then drive on a fresh loop from sync code.

    The convenience for the rare top-level sync caller whose Term compiles
    to an async-only Program: spins a loop via ``asyncio.run`` and drives
    the async path so the caller doesn't have to write an ``async def`` and
    import ``asyncio`` itself. Most callers should use ``arun`` directly.
    """
    return into_loop(arun(term, ctx, max_parallel=max_parallel))
