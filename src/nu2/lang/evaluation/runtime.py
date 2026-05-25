"""NuRuntime: the concrete Runtime that drives a compiled Nu Program.

Implements the engine's :class:`~nu2.engine.evaluation.Runtime` Protocol
and adds the Nu-specific runtime toolkit: a per-drive Budget, sequential
and parallel dispatch helpers, stream pumps, sentinel propagation, and
the hybrid sync/async fan-in that reads ``Attr.ON_LOOP``.

Hot-path contract: dispatch is one indexed call into the precompiled thunk
column -- ``program.thunks[nid](rt)`` (sync) or ``program.athunks[nid](rt)``
(async). Each thunk closes over its child thunks, so the inner recursion
runs closure-to-closure with no method lookup.

Layout:

- construction         -- program / ctx / budget binding
- dispatch             -- ``eval`` / ``aeval``
- sequential           -- ``eval_each`` / ``aeval_each``
- parallel             -- ``eval_parallel`` / ``aeval_parallel`` / ``aeval_race``
- streams              -- ``iter`` / ``aiter`` / ``collect`` / ``acollect`` / ``merge`` / ``amerge``
- boundary             -- ``in_thread`` / ``a_in_thread``
- sentinel propagation -- ``*_or_short`` family
- hybrid pump          -- ``amerge_hybrid`` (reads ``Attr.ON_LOOP``)
"""

from __future__ import annotations

import asyncio
import queue as _queue
from typing import TYPE_CHECKING

from .loop import safely_aclosing, safely_closing
from .sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import AsyncIterable, AsyncIterator, Callable, Iterable
    from concurrent.futures import Future

    from nu2.engine import Program

    from .budget import Budget

__all__ = ["NuRuntime"]


_DONE = object()


class NuRuntime:
    """Per-drive Runtime. Owns a Program, a Context, and a Budget."""

    __slots__ = ("budget", "ctx", "program")

    def __init__(self, program: Program, ctx: object, *, budget: Budget | None = None) -> None:
        from nu2.lang.evaluation.budget import Budget as _Budget

        self.program = program
        self.ctx = ctx
        self.budget = budget if budget is not None else _Budget()

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

    # --- sentinel-propagating parallel -------------------------------------

    def eval_parallel_or_short(self, nids: Iterable[int]) -> list | object:
        """Parallel ``eval`` with sentinel propagation; returns INVALID on any."""
        values = self.eval_parallel(nids)
        for v in values:
            if v is EMPTY or v is INVALID:
                return INVALID
        return values

    async def aeval_parallel_or_short(self, nids: Iterable[int]) -> list | object:
        """Async parallel with sentinel propagation."""
        values = await self.aeval_parallel(nids)
        for v in values:
            if v is EMPTY or v is INVALID:
                return INVALID
        return values

    # --- hybrid stream pump (reads Nu's ON_LOOP attribute) -----------------

    async def amerge_hybrid(self, nids: Iterable[int]) -> AsyncIterable:
        """Async-merge stream children with mixed sync/async per-child state.

        The canonical Par/Race case under a parallel async caller. Each
        child's ``Attr.ON_LOOP`` column decides its path: async-on-loop
        children drive their ``aiter`` cooperatively, sync children run on
        a worker thread via ``loop.run_in_executor``. Sync branches are
        semaphore-gated (each holds an OS thread); async branches don't gate.
        """
        from nu2.lang.structure.attrs import Attr

        nids = list(nids)
        on_loop_col = self.program.attrs[Attr.ON_LOOP]

        if self.budget.max_parallel == 1:
            for n in nids:
                if on_loop_col[n]:
                    async with safely_aclosing(await self.aiter(n)) as agen:
                        async for v in agen:
                            yield v
                else:
                    with safely_closing(self.iter(n)) as gen:
                        for v in gen:
                            yield v
            return

        if self.budget.thread_pool is None or self.budget.async_sem is None:
            msg = "amerge_hybrid requires a Budget allocated with async_mode and max_parallel > 1"
            raise RuntimeError(msg)
        loop = asyncio.get_running_loop()
        q: asyncio.Queue = asyncio.Queue()
        sem = self.budget.async_sem
        pool = self.budget.thread_pool

        def _drain_sync(n: int, loop_: asyncio.AbstractEventLoop) -> None:
            with safely_closing(self.iter(n)) as gen:
                for v in gen:
                    loop_.call_soon_threadsafe(q.put_nowait, v)

        async def run_child(n: int) -> None:
            try:
                if on_loop_col[n]:
                    async with safely_aclosing(await self.aiter(n)) as agen:
                        async for v in agen:
                            await q.put(v)
                else:
                    async with sem:
                        await loop.run_in_executor(pool, _drain_sync, n, loop)
            finally:
                await q.put(_DONE)

        tasks = [asyncio.create_task(run_child(n)) for n in nids]
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


async def _empty_aiter() -> AsyncIterator:
    """An empty async iterable."""
    if False:  # pragma: no cover
        yield
