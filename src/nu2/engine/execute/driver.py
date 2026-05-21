"""Runtime - the generic per-execution driver.

A thin object that walks a compiled Program, dispatches to each Symbol's
``eval`` / ``aeval`` method, and exposes a toolkit of helpers that atoms
use to recurse, inspect structure, and compose. Domain-free: knows nothing
of sentinels (the language layer's ``NuRuntime`` subclass adds those).

Three groups of helpers:

- **dispatch** - ``eval`` / ``aeval`` on a path.
- **sequential** - ``eval_each`` / ``eval_kids`` (and async siblings) for
  in-order evaluation.
- **parallel** - ``eval_parallel`` / ``aeval_parallel`` / ``aeval_race``
  for fan-out, plus ``merge`` / ``amerge`` / ``amerge_hybrid`` for stream
  interleaving (the hybrid covers the mixed sync/async per-child case).
  All gated by the Runtime's Budget; ``max_parallel == 1`` falls through
  to sequential.

Plus structure passthroughs (``children``, ``payload``, ``attr``) and
boundary helpers (``into_loop``, ``in_thread``, ``a_in_thread``).
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import AsyncIterable, AsyncIterator, Awaitable, Callable, Iterable
    from concurrent.futures import Future

    from nu2.engine.attribution import Program
    from nu2.engine.attribution.program import Path
    from nu2.engine.execute.budget import Budget
    from nu2.lang.context import Context

__all__ = ["Runtime"]


_DONE = object()


class Runtime:
    """Per-execution driver. Holds the compiled program, the Context, and a Budget.

    Atoms receive the Runtime as their first argument; they recurse via
    ``rt.eval(child_path)`` / ``rt.aeval(child_path)`` and inspect structure
    via ``rt.children`` / ``rt.payload`` / ``rt.attr``. Compositional atoms
    (Par, Race, Seq, ...) reach for the parallel/merge helpers.
    """

    __slots__ = ("budget", "ctx", "program")

    def __init__(self, program: Program, ctx: Context, *, budget: Budget | None = None) -> None:
        from nu2.engine.execute.budget import Budget as _Budget

        self.program = program
        self.ctx = ctx
        self.budget = budget if budget is not None else _Budget()

    # --- dispatch -----------------------------------------------------------

    def eval(self, path: Path = ()) -> object:
        """Evaluate the symbol at ``path``; return its value or None."""
        return self.program.symbol(path).eval(self, path)

    async def aeval(self, path: Path = ()) -> object:
        """Async-evaluate the symbol at ``path``; return its value or None."""
        return await self.program.symbol(path).aeval(self, path)

    # --- sequential ---------------------------------------------------------

    def eval_each(self, paths: Iterable[Path]) -> list:
        """Evaluate every given path in order; return the values."""
        return [self.eval(p) for p in paths]

    def eval_kids(self, path: Path) -> list:
        """Evaluate every child of ``path`` in order; return the values."""
        return self.eval_each(self.children(path))

    async def aeval_each(self, paths: Iterable[Path]) -> list:
        """Async-evaluate every given path in order; return the values."""
        return [await self.aeval(p) for p in paths]

    async def aeval_kids(self, path: Path) -> list:
        """Async-evaluate every child of ``path`` in order; return the values."""
        return await self.aeval_each(self.children(path))

    # --- parallel: values ---------------------------------------------------

    def eval_parallel(self, paths: Iterable[Path]) -> list:
        """Sync-parallel evaluation via the Budget's thread pool.

        Falls through to sequential when ``max_parallel == 1``. Values are
        returned in the order of ``paths`` regardless of completion order.
        """
        paths = list(paths)
        if self.budget.max_parallel == 1 or self.budget.thread_pool is None:
            return self.eval_each(paths)
        pool = self.budget.thread_pool
        futures = [pool.submit(self.eval, p) for p in paths]
        return [f.result() for f in futures]

    async def aeval_parallel(self, paths: Iterable[Path]) -> list:
        """Async-parallel evaluation via ``asyncio.gather``, semaphore-gated."""
        paths = list(paths)
        if self.budget.max_parallel == 1 or self.budget.async_sem is None:
            return await asyncio.gather(*(self.aeval(p) for p in paths))
        sem = self.budget.async_sem

        async def one(p: Path) -> object:
            async with sem:
                return await self.aeval(p)

        return await asyncio.gather(*(one(p) for p in paths))

    async def aeval_race(self, paths: Iterable[Path]) -> object:
        """Return the first child's value to complete; cancel the rest."""
        paths = list(paths)
        if not paths:
            msg = "aeval_race needs at least one path"
            raise ValueError(msg)
        tasks = [asyncio.create_task(self.aeval(p)) for p in paths]
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

    def merge(self, paths: Iterable[Path]) -> Iterable:
        """Sync-merge multiple stream children via the thread pool + queue.

        Yields values in completion order (unordered across children). Falls
        through to sequential per-child iteration when ``max_parallel == 1``.
        Each child iterable is wrapped with ``safely_closing`` so a caller's
        short-circuit finalizes every child stream.
        """
        import queue as _queue

        from nu2.engine.execute.loop import safely_closing

        paths = list(paths)
        if self.budget.max_parallel == 1 or self.budget.thread_pool is None:
            for p in paths:
                with safely_closing(self.iter(p)) as gen:
                    yield from gen
            return

        pool = self.budget.thread_pool
        q: _queue.Queue = _queue.Queue()

        def drain(p: Path) -> None:
            try:
                with safely_closing(self.iter(p)) as gen:
                    for v in gen:
                        q.put(v)
            finally:
                q.put(_DONE)

        futures = [pool.submit(drain, p) for p in paths]
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

    async def amerge(self, paths: Iterable[Path]) -> AsyncIterable:
        """Async-merge multiple stream children via tasks + asyncio.Queue.

        Yields values in completion order (unordered). Falls through to
        sequential per-child iteration when ``max_parallel == 1``. Each child
        async iterable is wrapped with ``safely_aclosing`` so a caller's
        short-circuit doesn't leak finalizer Tasks on the loop.
        """
        from nu2.engine.execute.loop import safely_aclosing

        paths = list(paths)
        if self.budget.max_parallel == 1:
            for p in paths:
                async with safely_aclosing(await self.aiter(p)) as agen:
                    async for v in agen:
                        yield v
            return

        q: asyncio.Queue = asyncio.Queue()

        async def drain(p: Path) -> None:
            try:
                async with safely_aclosing(await self.aiter(p)) as agen:
                    async for v in agen:
                        await q.put(v)
            finally:
                await q.put(_DONE)

        tasks = [asyncio.create_task(drain(p)) for p in paths]
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

    async def amerge_hybrid(self, paths: Iterable[Path]) -> AsyncIterable:
        """Async-merge stream children with mixed sync/async per-child state.

        The canonical Par/Race case under a parallel async caller. Each child's
        ``Attr.ON_LOOP`` decides its path: async-on-loop children drive their
        ``aiter`` cooperatively, sync children run their ``iter`` on a worker
        thread via ``loop.run_in_executor`` and forward into the same
        ``asyncio.Queue``. Sync branches are semaphore-gated (each holds an
        OS thread); async branches don't gate (the loop itself serializes).

        Falls through to sequential per-child iteration when
        ``max_parallel == 1``. Both sync and async branches are wrapped with
        ``safely_closing`` / ``safely_aclosing`` so a caller short-circuit
        finalizes every underlying generator.
        """
        from nu2.engine.execute.loop import safely_aclosing, safely_closing
        from nu2.lang.attrs import Attr

        paths = list(paths)

        def _on_loop(p: Path) -> bool:
            return bool(self.program.attr(p, Attr.ON_LOOP))

        if self.budget.max_parallel == 1:
            for p in paths:
                if _on_loop(p):
                    async with safely_aclosing(await self.aiter(p)) as agen:
                        async for v in agen:
                            yield v
                else:
                    with safely_closing(self.iter(p)) as gen:
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

        def _drain_sync(p: Path, loop_: asyncio.AbstractEventLoop) -> None:
            with safely_closing(self.iter(p)) as gen:
                for v in gen:
                    loop_.call_soon_threadsafe(q.put_nowait, v)

        async def run_child(p: Path) -> None:
            try:
                if _on_loop(p):
                    async with safely_aclosing(await self.aiter(p)) as agen:
                        async for v in agen:
                            await q.put(v)
                else:
                    async with sem:
                        await loop.run_in_executor(pool, _drain_sync, p, loop)
            finally:
                await q.put(_DONE)

        tasks = [asyncio.create_task(run_child(p)) for p in paths]
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

    def iter(self, path: Path) -> Iterable:
        """Iterable view of a stream-yielding child.

        Returns the raw iterable; the caller owns finalization. If you may
        short-circuit, wrap with ``safely_closing`` to guarantee the
        generator's frames are released. ``collect`` and ``merge`` do this
        for you.
        """
        result = self.eval(path)
        return result if result is not None else ()

    async def aiter(self, path: Path) -> AsyncIterable:
        """Async-iterable view of a stream-yielding child.

        Returns the raw async iterable. Short-circuiting iteration without
        ``safely_aclosing`` (or ``contextlib.aclosing``) leaks finalizer Tasks
        on the loop, retaining frames + Context. ``acollect`` / ``amerge`` do
        this for you.
        """
        result = await self.aeval(path)
        return result if result is not None else _empty_aiter()

    def collect(self, path: Path) -> list:
        """Materialize a stream child to a list.

        Wraps the child iterable with ``safely_closing`` so an exception
        mid-iteration still finalizes the generator.
        """
        from nu2.engine.execute.loop import safely_closing

        with safely_closing(self.iter(path)) as gen:
            return list(gen)

    async def acollect(self, path: Path) -> list:
        """Async-materialize a stream child to a list, with ``safely_aclosing``."""
        from nu2.engine.execute.loop import safely_aclosing

        out: list = []
        async with safely_aclosing(await self.aiter(path)) as agen:
            async for v in agen:
                out.append(v)
        return out

    # --- structure passthroughs --------------------------------------------

    def children(self, path: Path) -> list[Path]:
        """The child paths of ``path``."""
        return self.program.children(path)

    def payload(self, path: Path) -> dict:
        """The payload of the symbol at ``path``."""
        return self.program.payload(path)

    def attr(self, path: Path, name: str) -> object:
        """The compiled value of attribute ``name`` at ``path``."""
        return self.program.attr(path, name)

    # --- boundary helpers ---------------------------------------------------

    def into_loop(self, coro: Awaitable) -> object:
        """Run a coroutine to completion from inside sync ``eval``.

        Use sparingly; the schema's ``on_loop`` should make this unnecessary
        in well-formed programs. Escape hatch for ad-hoc bridges.
        """
        from nu2.engine.execute.loop import into_loop

        return into_loop(coro)

    def in_thread(self, fn: Callable, *args: object, **kwargs: object) -> Future:
        """Submit a blocking call to the Budget's thread pool; return the Future.

        Raises if ``max_parallel == 1`` (no pool was allocated).
        """
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
