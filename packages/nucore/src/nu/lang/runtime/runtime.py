"""Runtime: the concrete Runtime that drives a compiled Nu Program.

Implements the engine's :class:`~nu.engine.evaluation.Runtime` Protocol
and adds the Nu-specific runtime toolkit: a per-drive Budget, sequential
dispatch helpers, single-stream pumps, sentinel propagation, and the
thread-boundary primitives.

Hot-path contract: dispatch is one indexed call into the precompiled thunk
column: ``program.thunks[nid](rt)`` (sync) or ``program.athunks[nid](rt)``
(async). Each thunk closes over its child thunks, so the inner recursion
runs closure-to-closure with no method lookup.

Parallel/Race/AnyN fan-in and stream merge live in
``nu.core.flows.parallel._scheduling`` as free functions on ``rt`` - the
Parallel-family compiles hand child nids straight there, no Runtime hop.

Layout:

- construction:         program / ctx / budget binding
- dispatch:             ``eval`` / ``aeval``
- sequential:           ``eval_each`` / ``aeval_each``
- streams:              ``iter`` / ``aiter`` / ``collect`` / ``acollect``
- boundary:             ``in_thread`` / ``a_in_thread``
- sentinel propagation: ``*_or_short`` family
"""

from __future__ import annotations

import asyncio
import contextvars
from typing import TYPE_CHECKING

from nu.lang.sentinels import EMPTY, INVALID

from .utils.loop import safely_aclosing, safely_closing


if TYPE_CHECKING:
    from collections.abc import AsyncIterable, AsyncIterator, Callable, Iterable
    from concurrent.futures import Future

    from nu.engine import Program

    from .context import Context
    from .utils.budget import Budget

__all__ = ["Runtime"]

# Per-asyncio-task Context storage. Backed by ContextVar so brackets can
# `rt.ctx = scoped` around an `await` without contaminating sibling branches
# running under the same Runtime: each asyncio.Task inherits a copy-on-write
# view when spawned, and `.set()` inside the task is local to that task.
_RT_CTX: contextvars.ContextVar[Context] = contextvars.ContextVar("nu_rt_ctx")


def _carry_ctx() -> Callable[..., object]:
    """Return a runner that calls a function inside a copy of the caller's context.

    A worker thread starts with an empty contextvars context, so `_RT_CTX` is
    unset there and `Runtime.ctx` raises `LookupError`. Taking the copy on the
    calling side and submitting `copy.run` keeps the Context resolvable on the
    worker. A fresh copy per branch keeps a `.set()` inside that branch local to
    it, the same copy-on-write rule an asyncio.Task gets.
    """
    return contextvars.copy_context().run


class Runtime:
    """Per-drive Runtime. Owns a Program, a per-task Context, and a Budget."""

    __slots__ = ("budget", "program")

    def __init__(self, program: Program, ctx: Context, *, budget: Budget | None = None) -> None:
        from nu.lang.runtime.utils.budget import Budget as _Budget

        self.program = program
        _RT_CTX.set(ctx)
        self.budget = budget if budget is not None else _Budget()

    @property
    def ctx(self) -> Context:
        """The current asyncio-task-local Context."""
        return _RT_CTX.get()

    @ctx.setter
    def ctx(self, value: Context) -> None:
        _RT_CTX.set(value)

    # --- dispatch -----------------------------------------------------------

    def eval(self, nid: int = 0) -> object:
        """Evaluate the node at ``nid``; return its value or None.

        Dispatches through the precompiled thunk column. Each thunk has its
        child thunks captured in its closure, so the hot recursion runs
        thunk-to-thunk and never re-enters this method.
        """
        return self.program.thunks[nid](self)

    async def aeval(self, nid: int = 0) -> object:
        """Async-evaluate the node at ``nid``; return its value or None.

        Mirror of ``eval`` through the precompiled async thunk column.
        """
        return await self.program.athunks[nid](self)

    # --- sequential ---------------------------------------------------------

    def eval_each(self, nids: Iterable[int]) -> list:
        """Evaluate every given nid in order; return the values."""
        return [self.eval(n) for n in nids]

    async def aeval_each(self, nids: Iterable[int]) -> list:
        """Async-evaluate every given nid in order; return the values."""
        return [await self.aeval(n) for n in nids]

    # Parallel fan-in and stream merge live in
    # ``nu.core.flows.parallel._scheduling`` - free functions on ``rt``.

    # --- stream helpers -----------------------------------------------------

    def iter(self, nid: int) -> Iterable:
        """Iterable view of a stream-yielding child."""
        result = self.eval(nid)
        return result if result is not None else ()

    async def aiter(self, nid: int) -> AsyncIterable:
        """Async-iterable view of a stream-yielding child."""
        result = await self.aeval(nid)
        return result if result is not None else _empty_aiter()

    def collect(self, nid: int) -> list:
        """Materialize a stream child to a list."""
        with safely_closing(self.iter(nid)) as gen:
            return list(gen)

    async def acollect(self, nid: int) -> list:
        """Async-materialize a stream child to a list."""
        out: list = []
        async with safely_aclosing(await self.aiter(nid)) as agen:
            async for v in agen:
                out.append(v)
        return out

    # --- boundary helpers ---------------------------------------------------

    def in_thread(self, fn: Callable, *args: object, **kwargs: object) -> Future:
        """Submit a blocking call to the Budget's thread pool; return the Future."""
        if self.budget.thread_pool is None:
            msg = "in_thread requires max_parallel > 1"
            raise RuntimeError(msg)
        return self.budget.thread_pool.submit(_carry_ctx(), fn, *args, **kwargs)

    async def a_in_thread(self, fn: Callable, *args: object, **kwargs: object) -> object:
        """Await a blocking call on the Budget's thread pool."""
        if self.budget.thread_pool is None:
            msg = "a_in_thread requires max_parallel > 1"
            raise RuntimeError(msg)
        loop = asyncio.get_running_loop()
        run = _carry_ctx()
        if kwargs:
            return await loop.run_in_executor(
                self.budget.thread_pool,
                lambda: run(fn, *args, **kwargs),
            )
        return await loop.run_in_executor(self.budget.thread_pool, run, fn, *args)

    # --- sentinel-propagating evaluation -----------------------------------

    def eval_or_short(self, nids: Iterable[int]) -> list | object:
        """Evaluate every nid, short-circuiting on a sentinel.

        Implements the Query propagation rule: if any operand is EMPTY or
        INVALID, the result is INVALID. Otherwise returns the values list.
        """
        values: list = []
        eval_ = self.eval
        for n in nids:
            v = eval_(n)
            if v is EMPTY or v is INVALID:
                return INVALID
            values.append(v)
        return values

    async def aeval_or_short(self, nids: Iterable[int]) -> list | object:
        """Async variant of ``eval_or_short``."""
        values: list = []
        for n in nids:
            v = await self.aeval(n)
            if v is EMPTY or v is INVALID:
                return INVALID
            values.append(v)
        return values


async def _empty_aiter() -> AsyncIterator:
    """An empty async iterable."""
    if False:  # pragma: no cover
        yield
