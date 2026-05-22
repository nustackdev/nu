"""Runtime - the generic per-execution driver.

A thin object that walks an AttributedTerm by ``nid`` and dispatches to each
Term's ``eval`` / ``aeval`` method. Domain-free: knows nothing of sentinels
(the language layer's ``NuRuntime`` subclass adds those).

Hot-path contract: dispatch is one method call (``term.eval(rt, nid)``).
Atoms reach for their own ``self.children`` and ``self.payload`` and recurse
via ``rt.eval(cnid)``. Attribute reads go directly through
``rt.program.attrs[name][nid]``. The Runtime exposes only what the dispatcher
must do; trivial passthroughs are deleted.

Compositional helpers (``eval_each`` / ``eval_parallel`` / ``merge`` /
``amerge``) accept iterables of ``nid`` and do real work (pools, semaphores,
queues). Boundary helpers (``into_loop``, ``in_thread``, ``a_in_thread``)
stay; they are escape hatches, not passthroughs.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import AsyncIterable, AsyncIterator, Awaitable, Callable, Iterable
    from concurrent.futures import Future

    from nu2.engine.attribution import AttributedTerm
    from nu2.engine.evaluation.budget import Budget

__all__ = ["Runtime"]


_DONE = object()


class Runtime:
    """Per-execution driver. Holds the attributed program, the Context, and a Budget."""

    __slots__ = ("budget", "ctx", "program")

    def __init__(
        self, program: AttributedTerm, ctx: object, *, budget: Budget | None = None
    ) -> None:
        from nu2.engine.evaluation.budget import Budget as _Budget

        self.program = program
        self.ctx = ctx
        self.budget = budget if budget is not None else _Budget()

    # --- dispatch -----------------------------------------------------------

    def eval(self, nid: int = 0) -> object:
        """Evaluate the term at ``nid``; return its value or None.

        Dispatches through the compiled thunk column. Optimized atoms have
        baked their kid thunks into the closure, so the hot recursion runs
        thunk-to-thunk without revisiting this method.
        """
        return self.program.thunks[nid](self)

    async def aeval(self, nid: int = 0) -> object:
        """Async-evaluate the term at ``nid``; return its value or None.

        Dispatches through the compiled async thunk column, mirroring ``eval``.
        """
        return await self.program.athunks[nid](self)

    # --- sequential ---------------------------------------------------------

    def eval_each(self, nids: Iterable[int]) -> list:
        """Evaluate every given nid in order; return the values."""
        return [self.eval(n) for n in nids]

    async def aeval_each(self, nids: Iterable[int]) -> list:
        """Async-evaluate every given nid in order; return the values."""
        return [await self.aeval(n) for n in nids]

    # --- parallel: values ---------------------------------------------------

    def eval_parallel(self, nids: Iterable[int]) -> list:
        """Sync-parallel evaluation via the Budget's thread pool.

        Falls through to sequential when ``max_parallel == 1``. Values are
        returned in the order of ``nids`` regardless of completion order.
        """
        nids = list(nids)
        if self.budget.max_parallel == 1 or self.budget.thread_pool is None:
            return self.eval_each(nids)
        pool = self.budget.thread_pool
        futures = [pool.submit(self.eval, n) for n in nids]
        return [f.result() for f in futures]

    async def aeval_parallel(self, nids: Iterable[int]) -> list:
        """Async-parallel evaluation via ``asyncio.gather``, semaphore-gated."""
        nids = list(nids)
        if self.budget.max_parallel == 1 or self.budget.async_sem is None:
            return await asyncio.gather(*(self.aeval(n) for n in nids))
        sem = self.budget.async_sem

        async def one(n: int) -> object:
            async with sem:
                return await self.aeval(n)

        return await asyncio.gather(*(one(n) for n in nids))

    async def aeval_race(self, nids: Iterable[int]) -> object:
        """Return the first child's value to complete; cancel the rest."""
        nids = list(nids)
        if not nids:
            msg = "aeval_race needs at least one nid"
            raise ValueError(msg)
        tasks = [asyncio.create_task(self.aeval(n)) for n in nids]
        try:
            done, _ = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED,
            )
            return next(iter(done)).result()
        finally:
            for t in tasks:
                if not t.done():
                    t.cancel()
            for t in tasks:
                if not t.done():
                    try:
                        await t
                    except (asyncio.CancelledError, Exception):  # noqa: S110
                        pass

    # --- parallel: streams --------------------------------------------------

    def merge(self, nids: Iterable[int]) -> Iterable:
        """Sync-merge multiple stream children via the thread pool + queue.

        Yields values in completion order (unordered across children). Falls
        through to sequential per-child iteration when ``max_parallel == 1``.
        """
        import queue as _queue

        from nu2.engine.evaluation.loop import safely_closing

        nids = list(nids)
        if self.budget.max_parallel == 1 or self.budget.thread_pool is None:
            for n in nids:
                with safely_closing(self.iter(n)) as gen:
                    yield from gen
            return

        pool = self.budget.thread_pool
        q: _queue.Queue = _queue.Queue()

        def drain(n: int) -> None:
            try:
                with safely_closing(self.iter(n)) as gen:
                    for v in gen:
                        q.put(v)
            finally:
                q.put(_DONE)

        futures = [pool.submit(drain, n) for n in nids]
        remaining = len(futures)
        try:
            while remaining > 0:
                v = q.get()
                if v is _DONE:
                    remaining -= 1
                else:
                    yield v
        finally:
            for f in futures:
                f.cancel()

    async def amerge(self, nids: Iterable[int]) -> AsyncIterable:
        """Async-merge multiple stream children via tasks + asyncio.Queue."""
        from nu2.engine.evaluation.loop import safely_aclosing

        nids = list(nids)
        if self.budget.max_parallel == 1:
            for n in nids:
                async with safely_aclosing(await self.aiter(n)) as agen:
                    async for v in agen:
                        yield v
            return

        q: asyncio.Queue = asyncio.Queue()

        async def drain(n: int) -> None:
            try:
                async with safely_aclosing(await self.aiter(n)) as agen:
                    async for v in agen:
                        await q.put(v)
            finally:
                await q.put(_DONE)

        tasks = [asyncio.create_task(drain(n)) for n in nids]
        remaining = len(tasks)
        try:
            while remaining > 0:
                v = await q.get()
                if v is _DONE:
                    remaining -= 1
                else:
                    yield v
        finally:
            for t in tasks:
                if not t.done():
                    t.cancel()
            for t in tasks:
                try:
                    await t
                except (asyncio.CancelledError, Exception):  # noqa: S110
                    pass

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
        from nu2.engine.evaluation.loop import safely_closing

        with safely_closing(self.iter(nid)) as gen:
            return list(gen)

    async def acollect(self, nid: int) -> list:
        """Async-materialize a stream child to a list."""
        from nu2.engine.evaluation.loop import safely_aclosing

        out: list = []
        async with safely_aclosing(await self.aiter(nid)) as agen:
            async for v in agen:
                out.append(v)
        return out

    # --- boundary helpers ---------------------------------------------------

    def into_loop(self, coro: Awaitable) -> object:
        """Run a coroutine to completion from inside sync ``eval``."""
        from nu2.engine.evaluation.loop import into_loop

        return into_loop(coro)

    def in_thread(self, fn: Callable, *args: object, **kwargs: object) -> Future:
        """Submit a blocking call to the Budget's thread pool; return the Future."""
        if self.budget.thread_pool is None:
            msg = "in_thread requires max_parallel > 1"
            raise RuntimeError(msg)
        return self.budget.thread_pool.submit(fn, *args, **kwargs)

    async def a_in_thread(self, fn: Callable, *args: object, **kwargs: object) -> object:
        """Await a blocking call on the Budget's thread pool."""
        if self.budget.thread_pool is None:
            msg = "a_in_thread requires max_parallel > 1"
            raise RuntimeError(msg)
        loop = asyncio.get_running_loop()
        if kwargs:
            return await loop.run_in_executor(
                self.budget.thread_pool,
                lambda: fn(*args, **kwargs),
            )
        return await loop.run_in_executor(self.budget.thread_pool, fn, *args)


async def _empty_aiter() -> AsyncIterator:
    """An empty async iterable."""
    if False:  # pragma: no cover
        yield
