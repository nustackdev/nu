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

from tkv.tkv.storage import StorageProtocol
from utils import (
    TimingResult,
    get_counters,
    install_counters,
    print_results,
    timed_run,
    uninstall_counters,
)

import everypv as pv
from everybase import Context
from everybase.abc import Seq
from everypv import Atomic, auto_atomic
from everyshape import Shape


# ── Shapes ────────────────────────────────────────────────────────────


class BenchShape(Shape):
    f0 = pv.IntRef.slot()
    f1 = pv.IntRef.slot()
    f2 = pv.StrRef.slot()
    f3 = pv.FloatRef.slot()
    f4 = pv.IntRef.slot()


S = BenchShape

WRITES = [
    S.f0.set(1),
    S.f1.set(2),
    S.f2.set("val"),
    S.f3.set(0.1),
    S.f4.set(100),
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


async def bench_auto_atomic_per_term(ctx: Context) -> TimingResult:
    """auto_atomic wraps each Term individually (pre-built tree)."""
    await TERM_SEED.execute(ctx)  # warm up
    get_counters().reset()

    with timed_run(f"auto_atomic_per_term x{N}", N) as results:
        for _ in range(N):
            await TERM_AUTO_ATOMIC.execute(ctx)
    return results[0]


async def bench_single_atomic(ctx: Context) -> TimingResult:
    """Single manual Atomic wrapping all writes (pre-built tree)."""
    await TERM_SEED.execute(ctx)  # warm up
    get_counters().reset()

    with timed_run(f"single_atomic x{N}", N) as results:
        for _ in range(N):
            await TERM_SINGLE_ATOMIC.execute(ctx)
    return results[0]


async def bench_batched_atomic(ctx: Context, batch_size: int, term: Atomic) -> TimingResult:
    """Batched Atomic with batch_size ops per execute (pre-built tree)."""
    await TERM_SEED.execute(ctx)  # warm up
    get_counters().reset()

    n_executions = N // batch_size

    with timed_run(f"batched_atomic_bs{batch_size} x{N}", N) as results:
        for _ in range(n_executions):
            await term.execute(ctx)
    return results[0]


# ── Runner ───────────────────────────────────────────────────────────


async def run_all() -> list[TimingResult]:
    install_counters()
    results = []

    tmpdir = tempfile.mkdtemp(prefix="bench_atomic_")
    try:
        from everypv.adapters.storage import rocksdb_storage_inmemory

        with rocksdb_storage_inmemory(tmpdir) as storage:
            ctx = Context().with_handle(StorageProtocol, storage)

            results.append(await bench_auto_atomic_per_term(ctx))
            results.append(await bench_single_atomic(ctx))
            results.append(await bench_batched_atomic(ctx, 10, TERM_BATCH_10))
            results.append(await bench_batched_atomic(ctx, 50, TERM_BATCH_50))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    uninstall_counters()
    print_results("Atomic Granularity", results)
    return results


if __name__ == "__main__":
    asyncio.run(run_all())
