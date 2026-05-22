"""NuRuntime - Nu-flavored Runtime.

Extends the engine's generic ``Runtime`` with the sentinel propagation rule
(EMPTY/INVALID collapse to INVALID) and the hybrid stream pump that reads
``Attr.ON_LOOP`` to decide each child's sync/async path.

Hot path: sentinel checks are inline identity comparisons against the two
singleton objects ``EMPTY`` and ``INVALID`` (no isinstance, no function call).
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from nu2.engine.evaluation.driver import Runtime
from nu2.lang.evaluation.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import AsyncIterable, Iterable

__all__ = ["NuRuntime"]


_DONE = object()


class NuRuntime(Runtime):
    """Sentinel-aware Runtime. Adds the ``*_or_short`` toolkit on top of the engine."""

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
        from nu2.engine.evaluation.loop import safely_aclosing, safely_closing
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
