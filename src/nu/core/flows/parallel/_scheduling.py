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

``aeval_foreach_par`` is the odd one out: one body nid fanned out over a
runtime-sized list instead of a fixed set of children, each arm a loop task on
its own Context branch, off the budget entirely. It backs ``ForEachParAsync``,
which lives in ``nu.core.flows.control`` next to the ``ForEachDo`` it mirrors.

``aeval_foreach_reactive`` is the same fan-out kept open: the element list is
re-read rather than read once, so the arm set is a thing that is reconciled
instead of a thing that is built. It backs ``ForEachParReactive`` and takes its two
moving parts - how to read the elements, how to wait for the next change - as
callables, because both are Nu-level wiring the flow owns and neither is
scheduling.
"""

from __future__ import annotations

import asyncio
import queue as _queue
from typing import TYPE_CHECKING

from nu.lang.runtime.runtime import _carry_ctx
from nu.lang.runtime.utils.loop import safely_aclosing, safely_closing


if TYPE_CHECKING:
    from collections.abc import AsyncIterable, Awaitable, Callable, Iterable

    from nu.lang.runtime import Context, Runtime

__all__ = [
    "aeval_any",
    "aeval_foreach_par",
    "aeval_foreach_reactive",
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


# --- fan-out over a runtime list (loop only) -------------------------------


def _arm_ctx(ctx: Context, name: str, elem: object) -> Context:
    """Branch ``ctx`` for one arm, with ``elem`` bound under ``name``.

    The branch keeps its own attrs key space so sibling arms cannot stomp
    each other's loop variable, and shares every value by reference so a live
    handle sitting in attrs crosses the fan-out intact.
    """
    branch = ctx.branch()
    branch.attrs[name] = elem
    return branch


def _spawn_arm(rt: Runtime, nid: int, elem: object, name: str) -> asyncio.Task:
    """Start one arm of ``nid`` for ``elem``, on its own Context branch.

    The ``rt.ctx`` assignment has to happen inside the Task for the branch to
    stay arm-local, which is why this hands back a started Task rather than a
    coroutine for someone else to schedule.
    """

    async def arm(arm_ctx: Context) -> None:
        rt.ctx = arm_ctx
        await rt.aeval(nid)

    return asyncio.ensure_future(arm(_arm_ctx(rt.ctx, name, elem)))


async def aeval_foreach_par(rt: Runtime, nid: int, elems: Iterable, name: str) -> None:
    """Fan the body at ``nid`` out over ``elems``, one loop task each, joining on all.

    Every arm is an asyncio.Task holding its own Context branch with ``name``
    bound to its element. Placement is always the loop and the Budget is never
    touched: a parked coroutine costs no worker, so there is nothing here to
    ration. First error wins, as with ``aeval_parallel``, and the remaining
    arms are cancelled on the way out rather than left running headless.

    The task list is held until the join returns, so an arm that finishes early
    stays in it as a done Task. That is the right call for a fan-out that joins
    on all - the list is the join - and the wrong one for a supervisor, which
    is why ``aeval_foreach_reactive`` keeps its own book instead of reusing this.
    """
    elems = list(elems)
    if not elems:
        return

    tasks = [_spawn_arm(rt, nid, e, name) for e in elems]
    try:
        await asyncio.gather(*tasks)
    finally:
        await _settle(tasks)


def _forget_arm(arms: dict, key: object, task: asyncio.Task) -> None:
    """Drop a finished arm from the live set and take its outcome off it.

    Both halves matter. An arm left in the dict holds its Task alive and holds
    its key's slot against a later birth, and an arm that raised would warn at
    collection time if nobody ever read the exception. Reading it is also where
    the isolation happens: one arm's failure ends that arm and goes no further.
    """
    if arms.get(key) is task:
        del arms[key]
    if not task.cancelled():
        task.exception()


async def _reconcile_arms(
    rt: Runtime,
    nid: int,
    name: str,
    arms: dict,
    elems: Iterable,
) -> None:
    """Make ``arms`` hold exactly one live arm per element of ``elems``.

    An element with no arm gets one; an arm whose element is gone is cancelled
    and awaited here rather than left to unwind on its own time, so the key is
    genuinely free by the time this returns and a later birth can never overlap
    the death it followed. Every other arm is untouched, which is the point.

    Arms that already ended are swept first rather than waited on: a done
    callback lands a tick late, and a key whose arm is over should be free to
    be born again on this pass, not the one after it.
    """
    for key, task in [(k, t) for k, t in arms.items() if t.done()]:
        _forget_arm(arms, key, task)
    wanted = list(dict.fromkeys(elems))
    live = set(wanted)
    for key in [k for k in arms if k not in live]:
        await _settle([arms.pop(key)])
    for key in wanted:
        if key in arms:
            continue
        task = _spawn_arm(rt, nid, key, name)
        arms[key] = task
        task.add_done_callback(lambda t, k=key: _forget_arm(arms, k, t))


async def aeval_foreach_reactive(
    rt: Runtime,
    nid: int,
    name: str,
    elems_of: Callable[[], Awaitable[Iterable]],
    changed: Callable[[], Awaitable[object]],
) -> None:
    """Keep one arm of ``nid`` alive per element, reconciling on every change.

    Seeds from ``elems_of()``, then waits on ``changed()`` and reconciles
    again, forever. Arms are keyed by element, so a reconcile touches only the
    keys that moved: births and deaths, never the siblings. Elements must be
    hashable, since the key is what the book is kept by.

    It reconciles against the current element list rather than replaying the
    change that woke it, so a burst collapses into one pass and a delete and
    re-add that land between two passes are not seen at all. Nothing is missed
    by that: what the pass makes true is the answer to ``elems_of()`` as of the
    moment it ran.

    Returns only by cancellation - every arm is cancelled and drained on the
    way out. Errors do not propagate: an arm that raises ends alone, and its
    element gets a fresh arm on the next reconcile.
    """
    arms: dict[object, asyncio.Task] = {}
    try:
        while True:
            await _reconcile_arms(rt, nid, name, arms, await elems_of())
            await changed()
    finally:
        await _settle(list(arms.values()))


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
