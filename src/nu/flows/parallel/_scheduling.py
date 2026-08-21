"""Scheduling primitives for Parallel / Race / AnyN.

Free functions taking ``rt: Runtime`` as the first argument. Moved out of
``nu.lang.runtime.runtime`` so the Parallel-family compiles hand child nids
straight to the primitive that fits, no Runtime method hop in between.

Every primitive is placement-aware: the async variants read per-child mode
from three sources with this precedence:

1. ``force`` (class-level override from ``ParallelThreaded`` / ``ParallelAsync``
   and friends) - applied to every child.
2. ``per_child`` (an aligned tuple of ``"threaded"`` / ``"async"`` / ``None``
   given at construction via ``(child, "threaded")`` tuples).
3. ``Attr.ON_LOOP`` - the smart choice folded from the child's subtree.

``merge`` / ``amerge`` stay mode-agnostic - stream fan-in has no
Threaded/Async variants at this layer.
"""

from __future__ import annotations

import asyncio
import queue as _queue
from typing import TYPE_CHECKING

from nu.lang.runtime.runtime import _carry_ctx
from nu.lang.runtime.utils.loop import safely_aclosing, safely_closing


if TYPE_CHECKING:
    from collections.abc import AsyncIterable, Iterable

    from nu.lang.runtime import Runtime

__all__ = [
    "aeval_any",
    "aeval_parallel",
    "aeval_race",
    "amerge",
    "eval_parallel",
    "merge",
]


_DONE = object()


def _resolve_on_loop(
    on_loop_col: list, nid: int, i: int, per_child: tuple[str | None, ...] | None, force: str | None
) -> bool:
    """Return True if child ``nid`` at slot ``i`` should run on the loop.

    Precedence: ``force`` > ``per_child[i]`` > ``on_loop_col[nid]``.
    """
    if force is not None:
        return force == "async"
    if per_child is not None and per_child[i] is not None:
        return per_child[i] == "async"
    return bool(on_loop_col[nid])


# --- sync path ------------------------------------------------------------


def eval_parallel(
    rt: Runtime,
    nids: Iterable[int],
    *,
    per_child: tuple[str | None, ...] | None = None,
    force: str | None = None,
) -> list:
    """Sync-parallel evaluation via the Budget's thread pool.

    Falls through to sequential when ``max_parallel == 1``. Values are
    returned in the order of ``nids`` regardless of completion order. The
    ``per_child`` and ``force`` kwargs are accepted for API symmetry with
    the async primitives but have no effect on the sync path.
    """
    del per_child, force
    nids = list(nids)
    if rt.budget.max_parallel == 1 or rt.budget.thread_pool is None:
        return [rt.eval(n) for n in nids]
    pool = rt.budget.thread_pool
    futures = [pool.submit(_carry_ctx(), rt.eval, n) for n in nids]
    return [f.result() for f in futures]


# --- async placement ------------------------------------------------------


def _drive_async(
    rt: Runtime,
    nids: list[int],
    *,
    per_child: tuple[str | None, ...] | None = None,
    force: str | None = None,
) -> list:
    """Place each child per the precedence rule; return one awaitable each."""
    from nu.lang.attributes import Attr

    if rt.budget.thread_pool is None or rt.budget.async_sem is None:
        msg = "_drive_async requires a Budget allocated with async_mode and max_parallel > 1"
        raise RuntimeError(msg)
    loop = asyncio.get_running_loop()
    on_loop_col = rt.program.attrs[Attr.ON_LOOP]
    sem = rt.budget.async_sem
    pool = rt.budget.thread_pool

    async def place(i: int, n: int) -> object:
        on_loop = _resolve_on_loop(on_loop_col, n, i, per_child, force)
        async with sem:
            if on_loop:
                return await rt.aeval(n)
            return await loop.run_in_executor(pool, _carry_ctx(), rt.eval, n)

    return [place(i, n) for i, n in enumerate(nids)]


async def aeval_parallel(
    rt: Runtime,
    nids: Iterable[int],
    *,
    per_child: tuple[str | None, ...] | None = None,
    force: str | None = None,
) -> list:
    """Async-parallel join-all: gather every child, placement-aware.

    Falls through to a plain on-loop ``gather`` when ``max_parallel == 1``
    and no forcing/override needs a pool. Otherwise each child is placed
    per the precedence rule.
    """
    nids = list(nids)
    if rt.budget.max_parallel == 1 or rt.budget.async_sem is None:
        return await asyncio.gather(*(rt.aeval(n) for n in nids))
    return await asyncio.gather(*_drive_async(rt, nids, per_child=per_child, force=force))


async def _settle(tasks: Iterable) -> None:
    """Cancel any unfinished tasks and drain every one.

    Awaiting each task retrieves its outcome so no task is left with an
    unretrieved exception; callers have already taken the result they need.
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


async def aeval_race(
    rt: Runtime,
    nids: Iterable[int],
    *,
    per_child: tuple[str | None, ...] | None = None,
    force: str | None = None,
) -> object:
    """Return the first child's value to complete; cancel the rest."""
    nids = list(nids)
    if not nids:
        msg = "aeval_race needs at least one nid"
        raise ValueError(msg)
    if rt.budget.max_parallel == 1 or rt.budget.async_sem is None:
        coros: list = [rt.aeval(n) for n in nids]
    else:
        coros = _drive_async(rt, nids, per_child=per_child, force=force)
    tasks = [asyncio.ensure_future(c) for c in coros]
    try:
        done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        return next(iter(done)).result()
    finally:
        await _settle(tasks)


async def aeval_any(
    rt: Runtime,
    nids: Iterable[int],
    *,
    per_child: tuple[str | None, ...] | None = None,
    force: str | None = None,
) -> object:
    """Return the first child's value to succeed; cancel the rest.

    A child that raises is set aside and the wait continues. If every child
    fails, the last error is re-raised.
    """
    nids = list(nids)
    if not nids:
        msg = "aeval_any needs at least one nid"
        raise ValueError(msg)
    if rt.budget.max_parallel == 1 or rt.budget.async_sem is None:
        coros: list = [rt.aeval(n) for n in nids]
    else:
        coros = _drive_async(rt, nids, per_child=per_child, force=force)
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
        await _settle(tasks)


# --- parallel streams -----------------------------------------------------


def merge(rt: Runtime, nids: Iterable[int]) -> Iterable:
    """Sync-merge multiple stream children via the thread pool + queue.

    Yields values in completion order (unordered across children). Falls
    through to sequential per-child iteration when ``max_parallel == 1``.
    """
    nids = list(nids)
    if rt.budget.max_parallel == 1 or rt.budget.thread_pool is None:
        for n in nids:
            with safely_closing(rt.iter(n)) as gen:
                yield from gen
        return

    pool = rt.budget.thread_pool
    q: _queue.Queue = _queue.Queue()

    def drain(n: int) -> None:
        try:
            with safely_closing(rt.iter(n)) as gen:
                for v in gen:
                    q.put(v)
        finally:
            q.put(_DONE)

    futures = [pool.submit(_carry_ctx(), drain, n) for n in nids]
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


async def amerge(rt: Runtime, nids: Iterable[int]) -> AsyncIterable:
    """Async-merge stream children, placement-aware."""
    from nu.lang.attributes import Attr

    nids = list(nids)
    on_loop_col = rt.program.attrs[Attr.ON_LOOP]

    if rt.budget.max_parallel == 1:
        for n in nids:
            if on_loop_col[n]:
                async with safely_aclosing(await rt.aiter(n)) as agen:
                    async for v in agen:
                        yield v
            else:
                with safely_closing(rt.iter(n)) as gen:
                    for v in gen:
                        yield v
        return

    if rt.budget.thread_pool is None or rt.budget.async_sem is None:
        msg = "amerge requires a Budget allocated with async_mode and max_parallel > 1"
        raise RuntimeError(msg)
    loop = asyncio.get_running_loop()
    q: asyncio.Queue = asyncio.Queue()
    sem = rt.budget.async_sem
    pool = rt.budget.thread_pool

    def _drain_sync(n: int, loop_: asyncio.AbstractEventLoop) -> None:
        with safely_closing(rt.iter(n)) as gen:
            for v in gen:
                loop_.call_soon_threadsafe(q.put_nowait, v)

    async def run_child(n: int) -> None:
        try:
            if on_loop_col[n]:
                async with safely_aclosing(await rt.aiter(n)) as agen:
                    async for v in agen:
                        await q.put(v)
            else:
                async with sem:
                    await loop.run_in_executor(pool, _carry_ctx(), _drain_sync, n, loop)
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
