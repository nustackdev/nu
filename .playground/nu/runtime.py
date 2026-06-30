"""Runtime - entry layer + budget + the three pumps.

Sibling of `terms/`. Owns the host-level Γ realization (the Context) and
the pumps. `terms/*` never imports from here.

Algorithm:

- `tree_needs_loop` decides the top-level branch once.
- `_Budget` is installed in `ctx` for the entry's lifetime (idempotent).
- The producer's method is picked by `four_method_pick(nu, exec_state)`;
  Commands by `atom_dispatch`.
- Recursing into parallel nodes: `parallel_per_child` resolves each
  child's exec_state, `parallel_shape` picks the pump.
- Spans wrap their body's method via `span_dispatch`.

The hybrid pump (`_apump_hybrid`) gates sync branches on a thread +
semaphore slot; async branches don't gate; one async queue drains
both. `max_parallel == 1` falls through to sequential.

Public entry helpers (`execute`, `aexecute`, `first`, `afirst`, etc.)
drive new-core kinds via `four_method_pick` for producers and
`atom_dispatch` for Commands.
"""

from __future__ import annotations

import asyncio
import queue as _queue
from concurrent.futures import ThreadPoolExecutor
from contextlib import aclosing, closing
from typing import TYPE_CHECKING, Any

from .terms.command import Command
from .terms.dispatch import (
    ExecState,
    ParallelShape,
    atom_dispatch,
    parallel_per_child,
    parallel_shape,
    tree_needs_loop,
)
from .terms.flow import Flow
from .terms.realization import four_method_pick, realization_of
from .terms.span import Span
from .terms.types import Realization


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator

    from .context import Context
    from .terms.protocol import Nu


__all__ = [
    "_Budget",
    "_BudgetScope",
    "acollect",
    "aexecute",
    "afirst",
    "alast",
    "collect",
    "execute",
    "first",
]


_DONE = object()


# --- budget -----------------------------------------------------------------


class _Budget:
    """Execution budget: thread pool + concurrency gate for one run.

    Built at entry. Attached to Context and shared across child contexts
    produced during the run. Nested pumps read the same budget so
    `max_parallel` is tree-wide, not per-subtree.

    `max_parallel == 1` is the zero-concurrency case: no pool, no
    semaphore, pumps fall through to sequential. For `> 1` the async
    path uses an asyncio.Semaphore (gating both loop-resident async
    children and thread-dispatched sync children); the sync path uses a
    bounded ThreadPoolExecutor (pool size is the gate).
    """

    __slots__ = ("async_mode", "async_sem", "max_parallel", "thread_pool")

    def __init__(self, max_parallel: int, async_mode: bool) -> None:
        if max_parallel < 1:
            msg = f"max_parallel must be >= 1, got {max_parallel}"
            raise ValueError(msg)
        self.max_parallel = max_parallel
        self.async_mode = async_mode
        self.thread_pool: ThreadPoolExecutor | None = None
        self.async_sem: asyncio.Semaphore | None = None
        if max_parallel > 1:
            self.thread_pool = ThreadPoolExecutor(
                max_workers=max_parallel,
                thread_name_prefix="nu-worker",
            )
            if async_mode:
                self.async_sem = asyncio.Semaphore(max_parallel)

    def close(self) -> None:
        if self.thread_pool is not None:
            self.thread_pool.shutdown(wait=False, cancel_futures=True)
            self.thread_pool = None


class _BudgetScope:
    """Context manager: install `_Budget` on ctx for an entry's lifetime.

    If ctx already has a budget, this scope is a no-op (the outer entry
    owns the pool). Otherwise creates / attaches a budget and tears it
    down on exit.
    """

    __slots__ = ("_budget", "_ctx", "_owned")

    def __init__(
        self,
        ctx: Context,
        max_parallel: int,
        *,
        async_mode: bool,
    ) -> None:
        self._ctx = ctx
        existing = getattr(ctx, "_budget", None)
        if existing is not None:
            self._budget: _Budget | None = None
            self._owned = False
        else:
            self._budget = _Budget(max_parallel, async_mode)
            self._owned = True

    def __enter__(self) -> _BudgetScope:
        if self._owned:
            self._ctx._budget = self._budget
        return self

    def __exit__(self, *exc: object) -> None:
        if self._owned:
            try:
                if self._budget is not None:
                    self._budget.close()
            finally:
                self._ctx._budget = None


# --- pumps ------------------------------------------------------------------
#
# Three pumps mirror `dispatch.ParallelShape`:
#
# - `_pump_sync`    - all-no_loop. Thread pool when max_parallel > 1.
# - `_apump_async`  - all-loop. asyncio.gather over child tasks.
# - `_apump_hybrid` - mixed. Loop drives async children; sync children
#                     dispatch to thread pool; results coordinated
#                     through one shared async queue. Lifted verbatim
#                     from the legacy `_apump_parallel`.


def _pump_sync(
    parent: Nu,
    ctx: Context,
    child_states: list[ExecState],
) -> Generator[Any, None, None]:
    """Sync parallel pump. All children resolved to `no_loop`.

    `max_parallel == 1` (or no budget): sequentialize. Else each child
    runs on a worker thread; yields stream through a `queue.Queue`.
    """
    budget: _Budget | None = getattr(ctx, "_budget", None)
    max_par = budget.max_parallel if budget is not None else 1

    if max_par == 1:
        for child in parent._children:
            with closing(child.open(ctx)) as gen:
                yield from gen
        return

    pool = budget.thread_pool
    assert pool is not None  # noqa: S101
    q: _queue.Queue[Any] = _queue.Queue()

    def run_child(child: Nu) -> None:
        try:
            with closing(child.open(ctx)) as gen:
                for v in gen:
                    q.put(v)
        finally:
            q.put(_DONE)

    futures = [pool.submit(run_child, c) for c in parent._children]
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


async def _apump_async(
    parent: Nu,
    ctx: Context,
    child_states: list[ExecState],
) -> AsyncGenerator[Any, None]:
    """Async parallel pump. All children resolved to `loop`.

    `max_parallel == 1` falls through to sequential gather.
    """
    budget: _Budget | None = getattr(ctx, "_budget", None)
    max_par = budget.max_parallel if budget is not None else 1

    if max_par == 1:
        for child in parent._children:
            async with aclosing(child.aopen(ctx)) as gen:
                async for v in gen:
                    yield v
        return

    queue: asyncio.Queue[Any] = asyncio.Queue()

    async def run_child(child: Nu) -> None:
        try:
            async with aclosing(child.aopen(ctx)) as gen:
                async for v in gen:
                    await queue.put(v)
        finally:
            await queue.put(_DONE)

    tasks = [asyncio.create_task(run_child(c)) for c in parent._children]
    remaining = len(tasks)
    try:
        while remaining > 0:
            v = await queue.get()
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


def _pump_sync_into_async_queue(
    child: Nu,
    ctx: Context,
    loop: asyncio.AbstractEventLoop,
    queue: asyncio.Queue,
) -> None:
    """Run sync generator on a worker thread; forward to the loop queue.

    Helper for the hybrid pump.
    """
    with closing(child.open(ctx)) as gen:
        for v in gen:
            loop.call_soon_threadsafe(queue.put_nowait, v)


async def _apump_hybrid(
    parent: Nu,
    ctx: Context,
    child_states: list[ExecState],
) -> AsyncGenerator[Any, None]:
    """Hybrid parallel pump - the canonical mixed-state case.

    Async children run cooperatively on the loop (no semaphore - the
    loop itself is the shared resource). Sync children dispatch to a
    worker thread via `run_in_executor`; semaphore-gated because each
    sync branch holds a real OS thread and the pool is sized to
    `max_parallel`. One async queue drains both.

    `max_parallel == 1` falls through to sequential.

    Lifted from the legacy `Nu._apump_parallel` and adapted for
    explicit per-child states.
    """
    budget: _Budget | None = getattr(ctx, "_budget", None)
    max_par = budget.max_parallel if budget is not None else 1

    if max_par == 1:
        for child, state in zip(parent._children, child_states, strict=True):
            if state is ExecState.LOOP:
                async with aclosing(child.aopen(ctx)) as gen:
                    async for v in gen:
                        yield v
            else:
                with closing(child.open(ctx)) as gen:
                    for v in gen:
                        yield v
        return

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[Any] = asyncio.Queue()
    sem = budget.async_sem
    pool = budget.thread_pool
    assert sem is not None and pool is not None  # noqa: S101

    async def run_child(child: Nu, state: ExecState) -> None:
        try:
            if state is ExecState.LOOP:
                async with aclosing(child.aopen(ctx)) as gen:
                    async for v in gen:
                        await queue.put(v)
            else:
                async with sem:
                    await loop.run_in_executor(
                        pool,
                        _pump_sync_into_async_queue,
                        child,
                        ctx,
                        loop,
                        queue,
                    )
        finally:
            await queue.put(_DONE)

    tasks = [
        asyncio.create_task(run_child(c, s))
        for c, s in zip(parent._children, child_states, strict=True)
    ]
    remaining = len(tasks)
    try:
        while remaining > 0:
            v = await queue.get()
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


def pick_pump(
    parent: Nu,
    parent_state: ExecState,
) -> tuple[ParallelShape, list[ExecState]]:
    """Resolve per-child exec_states and pick the parallel shape."""
    child_states = [parallel_per_child(c, parent_state) for c in parent._children]
    return parallel_shape(child_states), child_states


# --- entry layer ------------------------------------------------------------
#
# These signatures preserve the legacy public surface (positional `nu`,
# positional `ctx`). The legacy module-level / method-level callers
# remain valid as long as a Context is in scope.


def _try_realization(nu: Nu) -> Realization | None:
    """Try to read the producer realization. None for non-producers (Commands etc.)."""
    try:
        return realization_of(nu)
    except TypeError:
        return None


def _is_command_body(nu: Nu) -> bool:
    """Whether the node is Command-shaped (recurses through Spans).

    Includes Flow (Strategy/Control) since those are CommandAtoms - they
    expose `run`/`arun`, no value yield.
    """
    if isinstance(nu, Span):
        return _is_command_body(nu._children[type(nu).body_slot])
    return isinstance(nu, (Command, Flow))


def _drive_sync(nu: Nu, ctx: Context) -> Generator[Any, None, None]:
    """Sync-drive a node, preferring new-core dispatch over `open`.

    - Command (or Span around a Command) -> `atom_dispatch`, no yield.
    - Scalar producer -> `four_method_pick` -> single-yield.
    - Stream producer or unknown -> `nu.open(ctx)`.
    """
    if _is_command_body(nu):
        atom_dispatch(nu, ExecState.NO_LOOP)(ctx)
        return
    real = _try_realization(nu)
    if real is Realization.SCALAR:
        v = four_method_pick(nu, ExecState.NO_LOOP)(ctx)
        yield v
        return
    if real is Realization.STREAM:
        with closing(nu.open(ctx)) as gen:
            yield from gen
        return
    # Unknown realization (e.g. legacy concrete kinds): fall back to open.
    with closing(nu.open(ctx)) as gen:
        yield from gen


async def _drive_async(nu: Nu, ctx: Context) -> AsyncGenerator[Any, None]:
    """Async-drive a node. Mirror of `_drive_sync`."""
    if _is_command_body(nu):
        await atom_dispatch(nu, ExecState.LOOP)(ctx)
        return
    real = _try_realization(nu)
    if real is Realization.SCALAR:
        v = await four_method_pick(nu, ExecState.LOOP)(ctx)
        yield v
        return
    if real is Realization.STREAM:
        async with aclosing(nu.aopen(ctx)) as gen:
            async for v in gen:
                yield v
        return
    async with aclosing(nu.aopen(ctx)) as gen:
        async for v in gen:
            yield v


def _default_ctx(ctx: Context | None) -> Context:
    if ctx is not None:
        return ctx
    from .context import Context as _Ctx

    return _Ctx()


def execute(
    nu: Nu,
    ctx: Context | None = None,
    *,
    max_parallel: int = 1,
) -> None:
    """Drain on the sync path. Subtree must not contain ASYNC-only atoms."""
    if tree_needs_loop(nu):
        msg = (
            f"{type(nu).__name__}: tree contains an async-only atom. "
            "Use aexecute / afirst / acollect."
        )
        raise RuntimeError(msg)
    ctx = _default_ctx(ctx)
    with _BudgetScope(ctx, max_parallel, async_mode=False):
        with closing(_drive_sync(nu, ctx)) as gen:
            for _ in gen:
                pass


def first(
    nu: Nu,
    ctx: Context | None = None,
    *,
    max_parallel: int = 1,
) -> Any:  # noqa: ANN401
    """First yield on the sync path."""
    if tree_needs_loop(nu):
        msg = f"{type(nu).__name__}: tree contains an async-only atom. Use afirst."
        raise RuntimeError(msg)
    ctx = _default_ctx(ctx)
    with _BudgetScope(ctx, max_parallel, async_mode=False):
        with closing(_drive_sync(nu, ctx)) as gen:
            for v in gen:
                return v
    msg = "nu yielded no values"
    raise RuntimeError(msg)


def collect(
    nu: Nu,
    ctx: Context | None = None,
    *,
    max_parallel: int = 1,
) -> list[Any]:
    """Drain into a list on the sync path."""
    if tree_needs_loop(nu):
        msg = f"{type(nu).__name__}: tree contains an async-only atom. Use acollect."
        raise RuntimeError(msg)
    ctx = _default_ctx(ctx)
    with _BudgetScope(ctx, max_parallel, async_mode=False):
        with closing(_drive_sync(nu, ctx)) as gen:
            return list(gen)


async def aexecute(
    nu: Nu,
    ctx: Context | None = None,
    *,
    max_parallel: int = 1,
) -> None:
    """Drain on the async path. Yields are discarded."""
    ctx = _default_ctx(ctx)
    with _BudgetScope(ctx, max_parallel, async_mode=True):
        async with aclosing(_drive_async(nu, ctx)) as agen:
            async for _ in agen:
                pass


async def afirst(
    nu: Nu,
    ctx: Context | None = None,
    *,
    max_parallel: int = 1,
) -> Any:  # noqa: ANN401
    """First yield on the async path."""
    ctx = _default_ctx(ctx)
    with _BudgetScope(ctx, max_parallel, async_mode=True):
        # Explicit aclose: short-circuiting `async for ... return v` leaves
        # the generator un-closed, making CPython's finalizer queue an
        # `agen.aclose()` Task on the loop. On a CPU-bound loop those
        # Tasks pile up retaining frames + ctx (real, observable leak).
        async with aclosing(_drive_async(nu, ctx)) as agen:
            async for v in agen:
                return v
    msg = "nu yielded no values"
    raise RuntimeError(msg)


async def alast(
    nu: Nu,
    ctx: Context | None = None,
    *,
    max_parallel: int = 1,
) -> Any:  # noqa: ANN401
    """Drain, return last yield."""
    ctx = _default_ctx(ctx)
    found = False
    val: Any = None
    with _BudgetScope(ctx, max_parallel, async_mode=True):
        async with aclosing(_drive_async(nu, ctx)) as agen:
            async for v in agen:
                val = v
                found = True
    if not found:
        msg = "nu yielded no values"
        raise RuntimeError(msg)
    return val


async def acollect(
    nu: Nu,
    ctx: Context | None = None,
    *,
    max_parallel: int = 1,
) -> list[Any]:
    """Drain into a list on the async path."""
    ctx = _default_ctx(ctx)
    out: list[Any] = []
    with _BudgetScope(ctx, max_parallel, async_mode=True):
        async with aclosing(_drive_async(nu, ctx)) as agen:
            async for v in agen:
                out.append(v)
    return out
