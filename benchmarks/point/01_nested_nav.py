"""Nested Shape Navigation -- read/write at different depths.

Measures: path navigation cost at depth 2/4/6.
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
from everypv import Atomic
from everyshape import Shape


# ── Shapes ────────────────────────────────────────────────────────────


class Level6(Shape):
    value = pv.IntRef.slot()
    label = pv.StrRef.slot()


class Level5(Shape):
    inner = pv.ShapeRef.slot(shape_type=Level6)
    count = pv.IntRef.slot()


class Level4(Shape):
    inner = pv.ShapeRef.slot(shape_type=Level5)
    count = pv.IntRef.slot()


class Level3(Shape):
    inner = pv.ShapeRef.slot(shape_type=Level4)
    count = pv.IntRef.slot()


class Level2(Shape):
    inner = pv.ShapeRef.slot(shape_type=Level3)
    count = pv.IntRef.slot()


class Root(Shape):
    inner = pv.ShapeRef.slot(shape_type=Level2)
    count = pv.IntRef.slot()


# ── Pre-built terms ──────────────────────────────────────────────────

TERMS = {
    "d2_write": Atomic(Root.inner.count.set(42)),
    "d4_write": Atomic(Root.inner.inner.inner.count.set(42)),
    "d6_write": Atomic(Root.inner.inner.inner.inner.inner.value.set(42)),
    "d2_read": Atomic(Root.inner.count.get()),
    "d4_read": Atomic(Root.inner.inner.inner.count.get()),
    "d6_read": Atomic(Root.inner.inner.inner.inner.inner.value.get()),
}

# Seed terms (write initial data so reads work)
SEEDS = {
    "d2": Atomic(Root.inner.count.set(42)),
    "d4": Atomic(Root.inner.inner.inner.count.set(42)),
    "d6": Atomic(Root.inner.inner.inner.inner.inner.value.set(42)),
}


# ── Benchmarks ───────────────────────────────────────────────────────

N = 100


async def bench_depth_2_write(ctx: Context) -> TimingResult:
    """Write at depth 2: Root.inner.count."""
    await SEEDS["d2"].execute(ctx)
    get_counters().reset()

    with timed_run(f"depth_2_write x{N}", N) as results:
        for _ in range(N):
            await TERMS["d2_write"].execute(ctx)
    return results[0]


async def bench_depth_4_write(ctx: Context) -> TimingResult:
    """Write at depth 4: Root.inner.inner.inner.count."""
    await SEEDS["d4"].execute(ctx)
    get_counters().reset()

    with timed_run(f"depth_4_write x{N}", N) as results:
        for _ in range(N):
            await TERMS["d4_write"].execute(ctx)
    return results[0]


async def bench_depth_6_write(ctx: Context) -> TimingResult:
    """Write at depth 6: Root.inner...inner.value."""
    await SEEDS["d6"].execute(ctx)
    get_counters().reset()

    with timed_run(f"depth_6_write x{N}", N) as results:
        for _ in range(N):
            await TERMS["d6_write"].execute(ctx)
    return results[0]


async def bench_depth_2_read(ctx: Context) -> TimingResult:
    """Read at depth 2: Root.inner.count."""
    await SEEDS["d2"].execute(ctx)
    get_counters().reset()

    with timed_run(f"depth_2_read x{N}", N) as results:
        for _ in range(N):
            await TERMS["d2_read"].execute(ctx)
    return results[0]


async def bench_depth_4_read(ctx: Context) -> TimingResult:
    """Read at depth 4: Root.inner.inner.inner.count."""
    await SEEDS["d4"].execute(ctx)
    get_counters().reset()

    with timed_run(f"depth_4_read x{N}", N) as results:
        for _ in range(N):
            await TERMS["d4_read"].execute(ctx)
    return results[0]


async def bench_depth_6_read(ctx: Context) -> TimingResult:
    """Read at depth 6: Root.inner...inner.value."""
    await SEEDS["d6"].execute(ctx)
    get_counters().reset()

    with timed_run(f"depth_6_read x{N}", N) as results:
        for _ in range(N):
            await TERMS["d6_read"].execute(ctx)
    return results[0]


# ── Runner ───────────────────────────────────────────────────────────


async def run_all() -> list[TimingResult]:
    install_counters()
    results = []

    tmpdir = tempfile.mkdtemp(prefix="bench_nested_")
    try:
        from everypv.adapters.storage import rocksdb_storage_inmemory

        with rocksdb_storage_inmemory(tmpdir) as storage:
            ctx = Context().with_handle(StorageProtocol, storage)

            results.append(await bench_depth_2_write(ctx))
            results.append(await bench_depth_4_write(ctx))
            results.append(await bench_depth_6_write(ctx))
            results.append(await bench_depth_2_read(ctx))
            results.append(await bench_depth_4_read(ctx))
            results.append(await bench_depth_6_read(ctx))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    uninstall_counters()
    print_results("Nested Shape Navigation", results)
    return results


if __name__ == "__main__":
    asyncio.run(run_all())
