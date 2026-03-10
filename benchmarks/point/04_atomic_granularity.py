"""Atomic Granularity -- transaction boundary overhead.

Compares: per-Term auto_atomic vs manual Atomic vs batched Atomic.
All term trees are pre-built. Benchmark loops measure only execution.
"""

from __future__ import annotations

import asyncio
import shutil
import sys
import tempfile


sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from utils import (
    TimingResult,
    get_counters,
    install_counters,
    print_results,
    timed_run,
    uninstall_counters,
)
from virtuals.tkv.storage import StorageProtocol

import eb_virtuals as ebv
from eb_virtuals import Atomic, auto_atomic
from everybase import Context
from everybase.abc import Seq
from everybase.shape import Shape


# ── Shapes ────────────────────────────────────────────────────────────


class BenchShape(Shape):
    f0 = ebv.IntRef.slot()
    f1 = ebv.IntRef.slot()
    f2 = ebv.StrRef.slot()
    f3 = ebv.FloatRef.slot()
    f4 = ebv.IntRef.slot()


S = BenchShape

WRITES = [
    S.f0.store(1),
    S.f1.store(2),
    S.f2.store("val"),
    S.f3.store(0.1),
    S.f4.store(100),
]


# ── Pre-built terms ──────────────────────────────────────────────────

TERM_AUTO_ATOMIC = auto_atomic(Seq(*WRITES))
TERM_SINGLE_ATOMIC = Atomic(Seq(*WRITES))
TERM_SEED = Atomic(Seq(*WRITES))

N = 200


def _build_batched_term(batch_size: int) -> Atomic:
    """Pre-build a batched Atomic with batch_size x 5 writes."""
    children = list(WRITES) * batch_size
    return Atomic(Seq(*children))


TERM_BATCH_10 = _build_batched_term(10)
TERM_BATCH_50 = _build_batched_term(50)


# ── Benchmarks ───────────────────────────────────────────────────────


async def _bench(label: str, loop_body, n_ops: int = N) -> TimingResult:
    """Benchmark with fresh db per measurement."""
    tmpdir = tempfile.mkdtemp(prefix="bench_atomic_")
    try:
        from eb_virtuals.presets import rocksdb_storage_inmemory

        with rocksdb_storage_inmemory(tmpdir) as storage:
            ctx = Context().bind(storage, StorageProtocol)
            await TERM_SEED.execute(ctx)  # warm up
            get_counters().reset()

            with timed_run(label, n_ops) as results:
                await loop_body(ctx)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


# ── Runner ───────────────────────────────────────────────────────────


async def run_all() -> list[TimingResult]:
    install_counters()
    results = []

    async def run_auto_atomic(ctx: Context) -> None:
        for _ in range(N):
            await TERM_AUTO_ATOMIC.execute(ctx)

    async def run_single_atomic(ctx: Context) -> None:
        for _ in range(N):
            await TERM_SINGLE_ATOMIC.execute(ctx)

    async def run_batched_10(ctx: Context) -> None:
        for _ in range(N // 10):
            await TERM_BATCH_10.execute(ctx)

    async def run_batched_50(ctx: Context) -> None:
        for _ in range(N // 50):
            await TERM_BATCH_50.execute(ctx)

    results.append(await _bench(f"auto_atomic_per_term x{N}", run_auto_atomic))
    results.append(await _bench(f"single_atomic x{N}", run_single_atomic))
    results.append(await _bench(f"batched_atomic_bs10 x{N}", run_batched_10))
    results.append(await _bench(f"batched_atomic_bs50 x{N}", run_batched_50))

    uninstall_counters()
    print_results("Atomic Granularity", results)
    return results


if __name__ == "__main__":
    asyncio.run(run_all())
