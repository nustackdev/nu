"""Nu - the primitive.

Nu is the recursive unit of computation. A Nu is made of Nus.
Both a leaf (`Literal(5)`) and a full app are Nus.

The single evaluator primitive is `aopen(ctx)` - a raw async generator
over Γ. Body = scope. Pre-first-yield = enter, each `yield` = a value
crossing the bracket, `finally` = exit. Yields 0..N times.

Composition:
    a >> b  = sequential - forward each child's stream in order
    a | b   = parallel   - interleave children's streams

Algebraic annotations on Nu (class-level):
    comm    = children commute (⟦⟧ invariant under reorder)
    indep   = children footprint-disjoint on writes
    assoc   = safe to re-associate nested Nus of the same kind

`can_parallelize()` returns `self.comm and self.indep`. Evaluator uses
this and only this to choose the pump (interleave vs sequential).

Hierarchy:
    Nu[T_co]                - base: runs children sequentially by default
    ├── NuIndepComm[T_co]   - parallel-capable composite (what `|` builds)
    ├── LValue[T_co]        - addressable location (internal)
    │   └── Ref[T_co]       - typed pointer (see ref.py)
    └── RValue[T_co]        - evaluable expression (internal)
        ├── Literal[T_co]   - literal data (see literal.py)
        └── Interaction[T_co]        - operation (see op.py)
"""

from __future__ import annotations

import asyncio
import queue as _queue
from abc import ABC
from concurrent.futures import ThreadPoolExecutor
from contextlib import aclosing, closing
from functools import cached_property
from typing import TYPE_CHECKING, Any, ClassVar, Generic, Self

from nu.tree.node import _Node

from .types import Mode, T_co, sup


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator

    from ..context import Context


__all__ = [
    "LValue",
    "Nu",
    "NuIndepComm",
    "RValue",
]


_DONE = object()


class _Budget:
    """Execution budget: thread pool + concurrency gate for one run.

    Built at entry (execute/aexecute/...). Attached to Context and shared
    across child contexts produced during the run. Nested pumps read the
    same budget so `max_parallel` is tree-wide, not per-subtree.

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
    """Context manager: install _Budget on ctx for an entry's lifetime.

    If ctx already has a budget, this scope is a no-op (outer entry
    owns the pool). Otherwise, creates/attaches a budget and tears it
    down on exit. Works with both `with` and sync entry methods; async
    entries use it as a plain `with` since budget lifecycle is sync.
    """

    __slots__ = ("_budget", "_ctx", "_owned")

    def __init__(self, ctx: Context, max_parallel: int, async_mode: bool) -> None:
        self._ctx = ctx
        existing = getattr(ctx, "_budget", None)
        if existing is not None:
            self._budget = None
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


def _pump_sync_into_async_queue(
    child: Nu,
    ctx: Context,
    loop: asyncio.AbstractEventLoop,
    queue: asyncio.Queue,
) -> None:
    """Run sync generator on a worker thread; forward yields to the loop's queue."""
    with closing(child.open(ctx)) as gen:
        for v in gen:
            loop.call_soon_threadsafe(queue.put_nowait, v)


class Nu(_Node["Nu"], Generic[T_co]):  # noqa: UP046
    """The primitive. Recursive unit of computation.

    Default `aopen`: runs children sequentially, forwards their yields.
    Subclasses override `aopen` for domain semantics.
    `Nu()` with no children is the identity (algebra's `0`).
    """

    # Algebraic annotations. Base defaults: assoc holds (re-grouping is safe
    # for the default sequential pump); comm and indep require declaration.
    comm: ClassVar[bool] = False
    indep: ClassVar[bool] = False
    assoc: ClassVar[bool] = True

    # own_mode — which of open / aopen the class has working.
    # SYNC: only open. ASYNC: only aopen. BOTH: both.
    # func_mode — execution mode of the core functionality.
    # SYNC: core is sync. ASYNC: core is async. BOTH: two first-class impls.
    # Valid pairs: (SYNC,SYNC), (BOTH,SYNC), (BOTH,BOTH), (ASYNC,ASYNC).
    # Concrete Interaction subclasses must declare both explicitly.
    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.BOTH

    def __init__(self, *children: object) -> None:
        """Wrap raw Python values as Literals; pass Nus through unchanged."""
        from .query import Literal

        wrapped: tuple[Nu, ...] = tuple(c if isinstance(c, Nu) else Literal(c) for c in children)
        super().__init__(*wrapped)

    def can_parallelize(self) -> bool:
        """Licenses the interleaving pump. comm ∧ indep."""
        return self.comm and self.indep

    @cached_property
    def effective_mode(self) -> Mode:
        """Subtree sup of own_mode. Cached per instance.

        Tells dispatch whether the subtree contains an ASYNC-only node.
        Sync entry points raise when this is ASYNC; async pump runs child
        sync when this is SYNC or BOTH.

        Nu trees are immutable post-construction; `_with_children`
        invalidates the cache for the clone.
        """
        child_modes = tuple(c.effective_mode for c in self._children)
        return sup(self.own_mode, *child_modes)

    def _with_children(self, *children: Nu) -> Self:
        clone = super()._with_children(*children)
        clone.__dict__.pop("effective_mode", None)
        return clone

    async def aopen(self, ctx: Context) -> AsyncGenerator[T_co, None]:
        """Run this Nu as a scope. Yields 0..N values.

        Default: dispatch by `can_parallelize()`.
        - True  -> interleave children's streams.
        - False -> forward each child's stream in order.
        """
        if self.can_parallelize():
            async for v in self._apump_parallel(ctx):
                yield v
        else:
            async for v in self._apump_sequential(ctx):
                yield v

    async def _adispatch_child(self, child: Nu, ctx: Context) -> AsyncGenerator[Any, None]:
        """Open a child on its most efficient path.

        If the child's effective_mode is ASYNC, use aopen. Otherwise run
        the child's sync generator inline — the child's sync path works,
        so no event loop needed.
        """
        if child.effective_mode is Mode.ASYNC:
            async with aclosing(child.aopen(ctx)) as gen:
                async for v in gen:
                    yield v
        else:
            with closing(child.open(ctx)) as gen:
                for v in gen:
                    yield v

    async def _apump_sequential(self, ctx: Context) -> AsyncGenerator[T_co, None]:
        for child in self._children:
            async for v in self._adispatch_child(child, ctx):
                yield v

    async def _apump_parallel(self, ctx: Context) -> AsyncGenerator[T_co, None]:
        """Parallel async pump.

        Dispatch per child by `effective_mode` and budget:
        - async child: runs on the loop via `create_task`.
        - sync child, budget > 1: runs on a worker thread via
          `run_in_executor`; its yields forward through the queue.
        - sync child, budget == 1 (or no budget): inlined as an async
          task (no thread), serialized by the `async_sem=None` path.

        `max_parallel == 1` falls through to sequential: no tasks, no
        threads, one child drained at a time. `async_sem` gates all
        concurrent launches when the budget allows more than one.
        """
        budget: _Budget | None = getattr(ctx, "_budget", None)
        max_par = budget.max_parallel if budget is not None else 1

        if max_par == 1:
            # No concurrency budget. Serialize.
            for child in self._children:
                async for v in self._adispatch_child(child, ctx):
                    yield v
            return

        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[Any] = asyncio.Queue()
        sem = budget.async_sem
        pool = budget.thread_pool
        assert sem is not None and pool is not None  # noqa: S101

        async def run_child(child: Nu) -> None:
            try:
                async with sem:
                    if child.effective_mode is Mode.ASYNC:
                        async for v in self._adispatch_child(child, ctx):
                            await queue.put(v)
                    else:
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

        tasks = [asyncio.create_task(run_child(c)) for c in self._children]
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

    # --- sync evaluator path ---

    def open(self, ctx: Context) -> Generator[T_co, None, None]:
        """Run as plain generator. Only valid when effective_mode ∈ {SYNC, BOTH}.

        Default: dispatch by `can_parallelize()`. Parallel-sync sequentializes
        (true thread parallelism goes through ExecutorRef, not the pump).
        """
        if self.effective_mode is Mode.ASYNC:
            msg = (
                f"{type(self).__name__} has ASYNC in its subtree; "
                "cannot run sync. Use aopen / aexecute."
            )
            raise RuntimeError(msg)
        if self.can_parallelize():
            yield from self._pump_parallel(ctx)
        else:
            yield from self._pump_sequential(ctx)

    def _pump_sequential(self, ctx: Context) -> Generator[T_co, None, None]:
        for child in self._children:
            yield from child.open(ctx)

    def _pump_parallel(self, ctx: Context) -> Generator[T_co, None, None]:
        """Parallel sync pump.

        `max_parallel == 1` (or no budget): sequentialize. Else each
        child runs on a worker thread from the bounded pool; yields
        stream through a `queue.Queue`. Pool size = max_parallel caps
        concurrency, no separate semaphore needed on this path.
        """
        budget: _Budget | None = getattr(ctx, "_budget", None)
        max_par = budget.max_parallel if budget is not None else 1

        if max_par == 1:
            for child in self._children:
                yield from child.open(ctx)
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

        futures = [pool.submit(run_child, c) for c in self._children]
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

    # --- consumption helpers (sugar over open) ---
    #
    # `max_parallel` is the only concurrency knob. Default 1 = no threads,
    # no semaphores, pumps sequentialize. > 1 spins up a ThreadPoolExecutor
    # for this run (torn down on exit) and gates concurrent children. The
    # budget is shared across child Contexts produced mid-run, so nested
    # `|` subtrees share one tree-wide budget.

    async def aexecute(self, ctx: Context | None = None, *, max_parallel: int = 1) -> None:
        """Drain. Yields are discarded. Empty Context if none passed."""
        ctx = self._default_ctx(ctx)
        with self._scoped_budget(ctx, max_parallel, async_mode=True):
            async with aclosing(self.aopen(ctx)) as gen:
                async for _ in gen:
                    pass

    def _check_sync_safe(self) -> None:
        """Eager guard at sync entry. Fails before any side effect."""
        if self.effective_mode is Mode.ASYNC:
            msg = (
                f"{type(self).__name__} has ASYNC in its subtree; "
                "cannot run sync. Use aexecute / afirst / acollect."
            )
            raise RuntimeError(msg)

    def execute(self, ctx: Context | None = None, *, max_parallel: int = 1) -> None:
        """Drain on the sync path. Subtree must not contain ASYNC nodes."""
        self._check_sync_safe()
        ctx = self._default_ctx(ctx)
        with self._scoped_budget(ctx, max_parallel, async_mode=False):
            for _ in self.open(ctx):
                pass

    def first(self, ctx: Context | None = None, *, max_parallel: int = 1) -> Any:  # noqa: ANN401
        """Take the first yield on the sync path. Subtree must not contain ASYNC nodes."""
        self._check_sync_safe()
        ctx = self._default_ctx(ctx)
        with self._scoped_budget(ctx, max_parallel, async_mode=False):
            for v in self.open(ctx):
                return v
        msg = "nu yielded no values"
        raise RuntimeError(msg)

    def collect(self, ctx: Context | None = None, *, max_parallel: int = 1) -> list[Any]:
        """Drain into a list on the sync path. Subtree must not contain ASYNC nodes."""
        self._check_sync_safe()
        ctx = self._default_ctx(ctx)
        with self._scoped_budget(ctx, max_parallel, async_mode=False):
            return list(self.open(ctx))

    async def adrain(self, ctx: Context | None = None, *, max_parallel: int = 1) -> None:
        """Alias for aexecute."""
        await self.aexecute(ctx, max_parallel=max_parallel)

    async def afirst(self, ctx: Context | None = None, *, max_parallel: int = 1) -> Any:  # noqa: ANN401
        """Take the first yield, close the rest."""
        ctx = self._default_ctx(ctx)
        with self._scoped_budget(ctx, max_parallel, async_mode=True):
            async with aclosing(self.aopen(ctx)) as gen:
                async for v in gen:
                    return v
        msg = "nu yielded no values"
        raise RuntimeError(msg)

    async def alast(self, ctx: Context | None = None, *, max_parallel: int = 1) -> Any:  # noqa: ANN401
        """Drain, return last yield."""
        ctx = self._default_ctx(ctx)
        found = False
        val: Any = None
        with self._scoped_budget(ctx, max_parallel, async_mode=True):
            async with aclosing(self.aopen(ctx)) as gen:
                async for v in gen:
                    val = v
                    found = True
        if not found:
            msg = "nu yielded no values"
            raise RuntimeError(msg)
        return val

    async def acollect(self, ctx: Context | None = None, *, max_parallel: int = 1) -> list[Any]:
        """Drain into a list."""
        ctx = self._default_ctx(ctx)
        out: list[Any] = []
        with self._scoped_budget(ctx, max_parallel, async_mode=True):
            async with aclosing(self.aopen(ctx)) as gen:
                async for v in gen:
                    out.append(v)
        return out

    @staticmethod
    def _default_ctx(ctx: Context | None) -> Context:
        if ctx is not None:
            return ctx
        from ..context import Context as _Ctx

        return _Ctx()

    @staticmethod
    def _scoped_budget(
        ctx: Context,
        max_parallel: int,
        *,
        async_mode: bool,
    ) -> _BudgetScope:
        """Install a budget on ctx for the entry's lifetime.

        Nested entries (rare) don't stack — if a budget is already
        attached, this is a no-op scope. The outer entry owns teardown.
        """
        return _BudgetScope(ctx, max_parallel, async_mode)

    # --- composition operators ---

    def __or__(self, other: object) -> Nu:
        """`a | b` -> parallel composition (NuIndepComm).

        Flattens when chained: `a | b | c` produces one NuIndepComm
        with three children.
        """
        if not isinstance(other, Nu):
            return NotImplemented  # type: ignore[return-value]
        if type(self) is NuIndepComm:
            return NuIndepComm(*self._children, other)
        return NuIndepComm(self, other)

    def __rshift__(self, other: object) -> Nu:
        """`a >> b` -> sequential composition (plain Nu).

        Flattens when chained: `a >> b >> c` produces one Nu with three
        children.
        """
        if not isinstance(other, Nu):
            return NotImplemented  # type: ignore[return-value]
        if type(self) is Nu:
            return Nu(*self._children, other)
        return Nu(self, other)


class NuIndepComm(Nu[T_co]):
    """Parallel-capable composite. Instantiated by `|`.

    Children run concurrently under the interleaving pump. Algebra
    annotations flipped to license it.
    """

    comm: ClassVar[bool] = True
    indep: ClassVar[bool] = True
    assoc: ClassVar[bool] = True


class LValue(Nu[T_co], ABC):
    """Addressable location. Internal base for Ref."""


class RValue(Nu[T_co], ABC):
    """Evaluable expression. Internal base for Literal and Interaction."""
