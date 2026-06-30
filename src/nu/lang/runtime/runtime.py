"""Runtime: the concrete Runtime that drives a compiled Nu Program.

Implements the engine's :class:`~nu.engine.evaluation.Runtime` Protocol
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
- parallel values      -- ``eval_parallel`` / ``aeval_parallel`` / ``aeval_race`` / ``aeval_any``
- parallel streams     -- ``merge`` / ``amerge``
- streams              -- ``iter`` / ``aiter`` / ``collect`` / ``acollect``
- boundary             -- ``in_thread`` / ``a_in_thread``
- sentinel propagation -- ``*_or_short`` family
- placement            -- ``_drive_async`` (reads ``Attr.ON_LOOP``); the async value
                          combinators and ``amerge`` share it
"""

from __future__ import annotations

import asyncio
import queue as _queue
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


_DONE = object()


class Runtime:
    """Per-drive Runtime. Owns a Program, a Context, and a Budget."""

    __slots__ = ("budget", "ctx", "program")

    def __init__(self, program: Program, ctx: Context, *, budget: Budget | None = None) -> None:
        from nu.lang.runtime.utils.budget import Budget as _Budget

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

    def _drive_async(self, nids: list[int]) -> list:
        """Place each child on the loop per ``Attr.ON_LOOP``; one awaitable each.

        The shared async placement for value fan-in. An async-on-loop child
        drives its ``aeval`` cooperatively; a sync child runs on a worker thread
        via ``run_in_executor``. Every branch is semaphore-gated, so total
        concurrency stays within ``max_parallel``. Each awaitable resolves to
        the child's value (sentinels included), in the order of ``nids``.

        Requires a Budget allocated with ``async_mode`` and ``max_parallel > 1``;
        the value combinators handle the sequential fall-through before calling.
        """
        from nu.lang.attributes import Attr

        if self.budget.thread_pool is None or self.budget.async_sem is None:
            msg = "_drive_async requires a Budget allocated with async_mode and max_parallel > 1"
            raise RuntimeError(msg)
        loop = asyncio.get_running_loop()
        on_loop_col = self.program.attrs[Attr.ON_LOOP]
        sem = self.budget.async_sem
        pool = self.budget.thread_pool

        async def place(n: int) -> object:
            async with sem:
                if on_loop_col[n]:
                    return await self.aeval(n)
                return await loop.run_in_executor(pool, self.eval, n)

        return [place(n) for n in nids]

    async def aeval_parallel(self, nids: Iterable[int]) -> list:
        """Async-parallel join-all: gather every child, placement-aware.

        Falls through to a plain on-loop ``gather`` when ``max_parallel == 1``
        (no pool to offload to); otherwise each child is placed via
        ``_drive_async`` (async on the loop, sync-only on a worker thread) so a
        mixed subtree runs hybrid rather than blocking the loop. Returns values
        in the order of ``nids``.
        """
        nids = list(nids)
        if self.budget.max_parallel == 1 or self.budget.async_sem is None:
            return await asyncio.gather(*(self.aeval(n) for n in nids))
        return await asyncio.gather(*self._drive_async(nids))

    async def _settle(self, tasks: Iterable) -> None:
        """Cancel any unfinished tasks and drain every one.

        Awaiting each task retrieves its outcome - a value, an exception, or a
        ``CancelledError`` - so no task is left with an unretrieved exception
        (which asyncio would log as a warning). Swallows everything: callers
        have already taken the result they care about.
        """
        tasks = list(tasks)
        for t in tasks:
            if not t.done():
                t.cancel()
        for t in tasks:
            try:
                await t
            except (asyncio.CancelledError, Exception):  # noqa: S110
                pass

    async def aeval_race(self, nids: Iterable[int]) -> object:
        """Return the first child's value to complete; cancel the rest.

        Placement-aware via ``_drive_async`` when ``max_parallel > 1``.
        """
        nids = list(nids)
        if not nids:
            msg = "aeval_race needs at least one nid"
            raise ValueError(msg)
        if self.budget.max_parallel == 1 or self.budget.async_sem is None:
            coros: list = [self.aeval(n) for n in nids]
        else:
            coros = self._drive_async(nids)
        tasks = [asyncio.ensure_future(c) for c in coros]
        try:
            done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            return next(iter(done)).result()
        finally:
            await self._settle(tasks)

    async def aeval_any(self, nids: Iterable[int]) -> object:
        """Return the first child's value to **succeed**; cancel the rest.

        First-success, not first-complete: a child that raises is set aside and
        the wait continues. If every child fails, the last error is re-raised.
        Placement-aware via ``_drive_async`` when ``max_parallel > 1``.
        """
        nids = list(nids)
        if not nids:
            msg = "aeval_any needs at least one nid"
            raise ValueError(msg)
        if self.budget.max_parallel == 1 or self.budget.async_sem is None:
            coros: list = [self.aeval(n) for n in nids]
        else:
            coros = self._drive_async(nids)
        tasks = [asyncio.ensure_future(c) for c in coros]
        pending = set(tasks)
        last_error: BaseException | None = None
        try:
            while pending:
                done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    exc = task.exception()
                    if exc is None:
                        return task.result()
                    last_error = exc
            if last_error is not None:
                raise last_error
            return None
        finally:
            await self._settle(tasks)

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

    # --- parallel: streams (async, reads Nu's ON_LOOP attribute) -----------

    async def amerge(self, nids: Iterable[int]) -> AsyncIterable:
        """Async-merge stream children, placement-aware - one async stream merge.

        The canonical Par/Race case over stream children under an async caller.
        Each child's ``Attr.ON_LOOP`` column decides its path: async-on-loop
        children drive their ``aiter`` cooperatively, sync children run on a
        worker thread via ``loop.run_in_executor``. Sync branches are
        semaphore-gated (each holds an OS thread); async branches don't gate,
        so a long-lived async stream never holds the semaphore for its lifetime.
        Yields in completion order (unordered across children).
        """
        from nu.lang.attributes import Attr

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
            msg = "amerge requires a Budget allocated with async_mode and max_parallel > 1"
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
