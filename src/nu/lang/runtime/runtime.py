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

- construction:         program / ctx / budget binding, ``branch``
- dispatch:             ``eval`` / ``aeval``
- sequential:           ``eval_each`` / ``aeval_each``
- streams:              ``iter`` / ``aiter`` / ``collect`` / ``acollect``
- boundary:             ``in_thread`` / ``a_in_thread``
- sentinel propagation: ``*_or_short`` family
"""

from __future__ import annotations

import asyncio
import contextvars
import functools
from typing import TYPE_CHECKING

from nu.lang.sentinels import EMPTY

from .utils.loop import safely_aclosing, safely_closing


if TYPE_CHECKING:
    from collections.abc import AsyncIterable, AsyncIterator, Callable, Iterable
    from concurrent.futures import Future

    from nu.engine import Program

    from .context import Context
    from .utils.budget import Budget

__all__ = ["Runtime"]


def _with_contextvars(fn: Callable) -> Callable:
    """``fn`` run inside a copy of the caller's Python contextvars, as ``asyncio.to_thread`` does.

    A pool thread starts with empty contextvars, so a var the caller set (an
    output capture, a trace id) would be unset where the work runs. Nu's own
    Context does not ride here: a thread arm gets it as ``rt.branch()``.
    """
    return functools.partial(contextvars.copy_context().run, fn)


class Runtime:
    """One task's Runtime: a Program, the task's own Context, and a shared Budget.

    ``ctx`` is fixed for the Runtime's life. Scopes inside the task open on
    the Context's stores; a task that starts runs on ``branch()``.
    """

    __slots__ = ("budget", "ctx", "program")

    def __init__(self, program: Program, ctx: Context, *, budget: Budget | None = None) -> None:
        from nu.lang.runtime.utils.budget import Budget as _Budget

        self.program = program
        self.ctx = ctx
        self.budget = budget if budget is not None else _Budget()

    def branch(self) -> Runtime:
        """The Runtime a starting task runs on: same Program and Budget, ``ctx.branch()``."""
        return Runtime(self.program, self.ctx.branch(), budget=self.budget)

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
        return self.budget.thread_pool.submit(_with_contextvars(fn), *args, **kwargs)

    async def a_in_thread(self, fn: Callable, *args: object, **kwargs: object) -> object:
        """Await a blocking call on the Budget's thread pool."""
        if self.budget.thread_pool is None:
            msg = "a_in_thread requires max_parallel > 1"
            raise RuntimeError(msg)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self.budget.thread_pool, _with_contextvars(functools.partial(fn, *args, **kwargs))
        )

    # --- sentinel-propagating evaluation -----------------------------------

    def eval_or_short(self, nids: Iterable[int]) -> list | object:
        """Evaluate every nid, short-circuiting on a sentinel.

        Implements the Query propagation rule: if any operand is EMPTY, the
        result is EMPTY. Otherwise returns the values list.
        """
        values: list = []
        eval_ = self.eval
        for n in nids:
            v = eval_(n)
            if v is EMPTY:
                return EMPTY
            values.append(v)
        return values

    async def aeval_or_short(self, nids: Iterable[int]) -> list | object:
        """Async variant of ``eval_or_short``."""
        values: list = []
        for n in nids:
            v = await self.aeval(n)
            if v is EMPTY:
                return EMPTY
            values.append(v)
        return values


async def _empty_aiter() -> AsyncIterator:
    """An empty async iterable."""
    if False:  # pragma: no cover
        yield
