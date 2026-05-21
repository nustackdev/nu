"""Top-level entry points: construct a Runtime, dispatch to the root, return.

Each entry owns a fresh ``Budget`` for the call, sized by ``max_parallel``,
and closes it on exit. The Runtime sees the Budget through construction; no
global state.

The sync entries (``eval``, ``first``, ``collect``, ``execute``) refuse a
program whose subtree carries an async-only atom (e.g. Watch); the caller
must use the async sibling. ``eval_in_loop`` is the deliberate bridge.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.context import Context
from nu2.lang.attrs import Attr
from nu2.runtime.budget import Budget
from nu2.runtime.driver import Runtime
from nu2.runtime.loop import into_loop, safely_aclosing, safely_closing


if TYPE_CHECKING:
    from nu2.attribute import Program
    from nu2.attribute.symbol import Symbol

__all__ = [
    "acollect",
    "aeval",
    "afirst",
    "alast",
    "arun",
    "collect",
    "eval",
    "eval_in_loop",
    "first",
    "run",
    "run_in_loop",
]


def _refuse_async_only(program: Program, entry: str, swap: str) -> None:
    """Raise if a sync entry sees an async-only subtree.

    Reads the root's ``Attr.HAS_ASYNC_ONLY_ATOM``. The cost is one attribute
    lookup; the check catches a Watch-bearing program before it tries to
    run on no loop and fails deep in dispatch.
    """
    if program.attr(program.root, Attr.HAS_ASYNC_ONLY_ATOM):
        msg = f"{entry}: program contains an async-only atom (e.g. Watch); use {swap}."
        raise RuntimeError(msg)


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
    _refuse_async_only(program, "eval", "aeval")
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


# --- stream entries -----------------------------------------------------
#
# For programs whose root yields a stream (StreamQuery). Each opens the root
# value through the Runtime's iter / aiter, wraps it with safely_closing /
# safely_aclosing so a short-circuit (first, partial collect) still finalizes
# the underlying generator, and tears the Budget down on exit.


def first(
    program: Program,
    ctx: Context | None = None,
    *,
    max_parallel: int = 1,
) -> tuple[object, Context]:
    """Return the first item of a stream-rooted program; ``(value, ctx)``.

    Raises ``RuntimeError`` if the stream is empty.
    """
    _refuse_async_only(program, "first", "afirst")
    ctx = ctx if ctx is not None else Context()
    with Budget(max_parallel, async_mode=False) as budget:
        rt = Runtime(program, ctx, budget=budget)
        with safely_closing(rt.iter(program.root)) as gen:
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
    """Materialize a stream-rooted program to a list; ``(values, ctx)``."""
    _refuse_async_only(program, "collect", "acollect")
    ctx = ctx if ctx is not None else Context()
    with Budget(max_parallel, async_mode=False) as budget:
        rt = Runtime(program, ctx, budget=budget)
        return rt.collect(program.root), ctx


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
        async with safely_aclosing(await rt.aiter(program.root)) as agen:
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
    """Drain a stream-rooted program and return the last item; ``(value, ctx)``.

    Raises ``RuntimeError`` if the stream is empty.
    """
    ctx = ctx if ctx is not None else Context()
    found = False
    last: object = None
    with Budget(max_parallel, async_mode=True) as budget:
        rt = Runtime(program, ctx, budget=budget)
        async with safely_aclosing(await rt.aiter(program.root)) as agen:
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
        return await rt.acollect(program.root), ctx


# --- description-level convenience --------------------------------------
#
# The all-in-one entry: take a description (Symbol), compile it against the
# Nu schema, validate against the Nu law set, then drive. Three phases in
# one call - what app code actually wants. The compile/validate pieces are
# still available standalone via ``nu2.lang`` for callers that want a
# Program in hand (e.g. for static inspection).


def run(
    description: Symbol,
    ctx: Context | None = None,
    *,
    max_parallel: int = 1,
) -> tuple[object, Context]:
    """Compile a description, validate it, evaluate it; return ``(value, ctx)``.

    Args:
        description: a Nu description (any ``Symbol``).
        ctx: the Context to drive against; a fresh one if omitted.
        max_parallel: tree-wide concurrency gate. ``1`` is sequential.

    Returns:
        The value the root produced (None for effect-only programs) and the
        Context after execution.

    Raises:
        ValueError: the description fails Nu law validation.
        RuntimeError: the program subtree contains an async-only atom; use
            ``arun`` instead.
    """
    from nu2.lang import LAWS, compile, validate

    program = validate(compile(description), *LAWS)
    return eval(program, ctx, max_parallel=max_parallel)


async def arun(
    description: Symbol,
    ctx: Context | None = None,
    *,
    max_parallel: int = 1,
) -> tuple[object, Context]:
    """Async sibling of ``run``: compile, validate, then ``aeval``."""
    from nu2.lang import LAWS, compile, validate

    program = validate(compile(description), *LAWS)
    return await aeval(program, ctx, max_parallel=max_parallel)


def run_in_loop(
    description: Symbol,
    ctx: Context | None = None,
    *,
    max_parallel: int = 1,
) -> tuple[object, Context]:
    """Compile, validate, then drive on a fresh loop from sync code.

    The convenience for the rare top-level sync caller whose description
    contains an async-only atom: spins a loop via ``asyncio.run`` and drives
    the async path so the caller doesn't have to write an ``async def`` and
    import ``asyncio`` itself. Most callers should use ``arun`` directly.
    """
    return into_loop(arun(description, ctx, max_parallel=max_parallel))
