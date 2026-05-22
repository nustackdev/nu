"""NuRuntime - Nu-flavored Runtime.

Extends the engine's generic ``Runtime`` with the parts that depend on Nu's
vocabulary: the sentinel propagation rule (EMPTY/INVALID collapse to INVALID),
and the hybrid stream pump that reads ``Attr.ON_LOOP`` to decide each child's
sync/async path. The variants below mirror the generic toolkit one-for-one.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from nu2.engine.evaluation.driver import Runtime


if TYPE_CHECKING:
    from collections.abc import AsyncIterable, Iterable

    from nu2.engine.attribution.attributed_term import Path

__all__ = ["NuRuntime"]


_DONE = object()


class NuRuntime(Runtime):
    """Sentinel-aware Runtime. Adds the ``*_or_short`` toolkit on top of the engine.

    Atoms in Nu's standard core (``nu2.core``) receive a ``NuRuntime`` from
    ``lang.entry``; they use ``rt.eval_kids_or_short`` etc. to participate in
    the Query propagation rule. Sequential and parallel variants are provided.
    """

    # --- sentinel-propagating evaluation -----------------------------------

    def eval_or_short(self, paths: Iterable[Path]) -> list | object:
        """Evaluate every path, short-circuiting on a sentinel.

        Implements the Query propagation rule: if any operand is EMPTY or
        INVALID, the result is INVALID. Otherwise returns the values list.

        Use in a ScalarQuery's ``eval``::

            values = rt.eval_or_short(rt.children(path))
            return values if is_sentinel(values) else sum(values)
        """
        from nu2.lang.sentinels import INVALID, is_sentinel

        values: list = []
        for p in paths:
            v = self.eval(p)
            if is_sentinel(v):
                return INVALID
            values.append(v)
        return values

    async def aeval_or_short(self, paths: Iterable[Path]) -> list | object:
        """Async variant of ``eval_or_short``."""
        from nu2.lang.sentinels import INVALID, is_sentinel

        values: list = []
        for p in paths:
            v = await self.aeval(p)
            if is_sentinel(v):
                return INVALID
            values.append(v)
        return values

    def eval_kids_or_short(self, path: Path) -> list | object:
        """Sugar: ``eval_or_short(rt.children(path))``."""
        return self.eval_or_short(self.children(path))

    async def aeval_kids_or_short(self, path: Path) -> list | object:
        """Sugar: ``aeval_or_short(rt.children(path))``."""
        return await self.aeval_or_short(self.children(path))

    # --- sentinel-propagating parallel -------------------------------------

    def eval_parallel_or_short(self, paths: Iterable[Path]) -> list | object:
        """Parallel ``eval`` with sentinel propagation; returns INVALID on any.

        Branches still all run (they have already been dispatched to the pool);
        the propagation rule applies to the aggregated result.
        """
        from nu2.lang.sentinels import INVALID, is_sentinel

        values = self.eval_parallel(paths)
        return INVALID if any(is_sentinel(v) for v in values) else values

    async def aeval_parallel_or_short(self, paths: Iterable[Path]) -> list | object:
        """Async parallel with sentinel propagation."""
        from nu2.lang.sentinels import INVALID, is_sentinel

        values = await self.aeval_parallel(paths)
        return INVALID if any(is_sentinel(v) for v in values) else values

    # --- hybrid stream pump (reads Nu's ON_LOOP attribute) -----------------

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
        from nu2.engine.evaluation.loop import safely_aclosing, safely_closing
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
