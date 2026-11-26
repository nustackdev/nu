"""Runtime: the concrete Runtime that drives a compiled Nu Program.

Implements the engine's :class:`~nu.engine.evaluation.Runtime` Protocol
and adds the Nu-specific runtime toolkit: a per-drive Budget, sequential
dispatch helpers, single-stream pumps, and the thread-boundary primitives.

Hot-path contract: dispatch is one indexed call into the precompiled thunk
column: ``program.thunks[nid](rt)`` (sync) or ``program.athunks[nid](rt)``
(async). Each thunk closes over its child thunks, so the inner recursion
runs closure-to-closure with no method lookup.

Parallel/Race/AnyN fan-in and stream merge live in
``nu.core.flows.parallel._scheduling`` as free functions on ``rt`` - the
Parallel-family compiles hand child nids straight there, no Runtime hop.

Layout:

- construction:         program / ctx / budget binding, ``on``
- dispatch:             ``eval`` / ``aeval``
- sequential:           ``eval_each`` / ``aeval_each``
- streams:              ``iter`` / ``aiter`` / ``collect`` / ``acollect``
- boundary:             ``in_thread`` / ``a_in_thread``
"""

from __future__ import annotations

import asyncio
import contextvars
import functools
from typing import TYPE_CHECKING

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
    Context does not ride here: a thread arm gets it through its ``rt``.
    """
    return functools.partial(contextvars.copy_context().run, fn)


class Runtime:
    """A Program, the Context it runs on, and a shared Budget.

    ``ctx`` is fixed for the Runtime's life. A scope that pushes a frame runs
    its body on ``on(new_ctx)``, a derived Runtime; children just get that
    one. Anything holding a Runtime (a stream, a delayed task) keeps its
    frames alive.
    """

    __slots__ = ("budget", "ctx", "program")

    def __init__(self, program: Program, ctx: Context, *, budget: Budget | None = None) -> None:
        from nu.lang.runtime.utils.budget import Budget as _Budget

        self.program = program
        self.ctx = ctx
        self.budget = budget if budget is not None else _Budget()

    def on(self, ctx: Context) -> Runtime:
        """The Runtime running on ``ctx``: same Program and Budget.

        Returns ``self`` when ``ctx`` is already this Runtime's Context.
        """
        if ctx is self.ctx:
            return self
        return Runtime(self.program, ctx, budget=self.budget)

    def _fork_attrs(self) -> Runtime:
        """This Runtime with its own attrs table, for a concurrent arm.

        TEMPORARY (task-184 phase 4 deletes attrs and this with it): the
        frames are shared, only the attrs table is copied, so a name an arm
        binds in attrs stays in the arm.
        """
        return Runtime(self.program, self.ctx._fork_attrs(), budget=self.budget)

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


async def _empty_aiter() -> AsyncIterator:
    """An empty async iterable."""
    if False:  # pragma: no cover
        yield
