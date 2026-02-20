"""Scenario 2: Nested Shape Navigation — read/write at different depths.

Measures: get_node_info, ensure_created, path navigation, Shape.__getattribute__.
Varies: nesting depth (2, 4, 6 levels), number of operations.
"""

from __future__ import annotations

import asyncio
import shutil
import sys
import tempfile


sys.path.insert(0, "benchmarks")

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


# --------------------------------------------------------------------------
# Shapes — varying nesting depth
# --------------------------------------------------------------------------


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


# --------------------------------------------------------------------------
# Benchmarks
# --------------------------------------------------------------------------


async def bench_depth_2_write(ctx: Context, n: int) -> TimingResult:
    """Write at depth 2: Root.inner.count"""
    await Atomic(Root.inner.count.set(0)).execute(ctx)
    get_counters().reset()

    with timed_run(f"depth_2_write x{n}", n) as results:
        for i in range(n):
            await Atomic(Root.inner.count.set(i)).execute(ctx)
    return results[0]


async def bench_depth_4_write(ctx: Context, n: int) -> TimingResult:
    """Write at depth 4: Root.inner.inner.inner.count"""
    await Atomic(Root.inner.inner.inner.count.set(0)).execute(ctx)
    get_counters().reset()

    with timed_run(f"depth_4_write x{n}", n) as results:
        for i in range(n):
            await Atomic(Root.inner.inner.inner.count.set(i)).execute(ctx)
    return results[0]


async def bench_depth_6_write(ctx: Context, n: int) -> TimingResult:
    """Write at depth 6: Root.inner.inner.inner.inner.inner.value"""
    await Atomic(Root.inner.inner.inner.inner.inner.value.set(0)).execute(ctx)
    get_counters().reset()

    with timed_run(f"depth_6_write x{n}", n) as results:
        for i in range(n):
            await Atomic(Root.inner.inner.inner.inner.inner.value.set(i)).execute(ctx)
    return results[0]


async def bench_depth_2_read(ctx: Context, n: int) -> TimingResult:
    """Read at depth 2: Root.inner.count"""
    await Atomic(Root.inner.count.set(42)).execute(ctx)
    get_counters().reset()

    with timed_run(f"depth_2_read x{n}", n) as results:
        for _ in range(n):
            await Atomic(Root.inner.count.get()).execute(ctx)
    return results[0]


async def bench_depth_4_read(ctx: Context, n: int) -> TimingResult:
    """Read at depth 4: Root.inner.inner.inner.count"""
    await Atomic(Root.inner.inner.inner.count.set(42)).execute(ctx)
    get_counters().reset()

    with timed_run(f"depth_4_read x{n}", n) as results:
        for _ in range(n):
            await Atomic(Root.inner.inner.inner.count.get()).execute(ctx)
    return results[0]


async def bench_depth_6_read(ctx: Context, n: int) -> TimingResult:
    """Read at depth 6: Root.inner.inner.inner.inner.inner.value"""
    await Atomic(Root.inner.inner.inner.inner.inner.value.set(42)).execute(ctx)
    get_counters().reset()

    with timed_run(f"depth_6_read x{n}", n) as results:
        for _ in range(n):
            await Atomic(Root.inner.inner.inner.inner.inner.value.get()).execute(ctx)
    return results[0]


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------

N = 100


async def run_all() -> list[TimingResult]:
    install_counters()
    results = []

    tmpdir = tempfile.mkdtemp(prefix="bench_nested_")
    try:
        from everypv.adapters.storage import rocksdb_storage_inmemory

        with rocksdb_storage_inmemory(tmpdir) as storage:
            ctx = Context().with_handle(StorageProtocol, storage)

            results.append(await bench_depth_2_write(ctx, N))
            results.append(await bench_depth_4_write(ctx, N))
            results.append(await bench_depth_6_write(ctx, N))
            results.append(await bench_depth_2_read(ctx, N))
            results.append(await bench_depth_4_read(ctx, N))
            results.append(await bench_depth_6_read(ctx, N))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    uninstall_counters()
    print_results("Scenario 2: Nested Shape Navigation", results)
    return results


if __name__ == "__main__":
    asyncio.run(run_all())
