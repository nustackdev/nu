"""Scenario 1: Flat Writes — pure write throughput for primitive fields.

Measures: auto_atomic overhead, RocksDB put, container create for flat shapes.
Varies: number of fields per operation, total operations.
"""

from __future__ import annotations

import asyncio
import sys


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
from everybase.abc import Seq
from everypv import Atomic, auto_atomic
from everyshape import Shape


# --------------------------------------------------------------------------
# Shapes
# --------------------------------------------------------------------------


class FlatShape(Shape):
    f0 = pv.IntRef.slot()
    f1 = pv.IntRef.slot()
    f2 = pv.StrRef.slot()
    f3 = pv.FloatRef.slot()
    f4 = pv.BoolRef.slot()
    f5 = pv.IntRef.slot()
    f6 = pv.StrRef.slot()
    f7 = pv.FloatRef.slot()
    f8 = pv.IntRef.slot()
    f9 = pv.StrRef.slot()


S = FlatShape


# --------------------------------------------------------------------------
# Benchmarks
# --------------------------------------------------------------------------


async def bench_single_field_write(ctx: Context, n: int) -> TimingResult:
    """Write a single int field N times (each in its own Atomic)."""
    # Warm up: ensure container exists
    await Atomic(S.f0.set(0)).execute(ctx)
    get_counters().reset()

    with timed_run(f"single_field x{n}", n) as results:
        for i in range(n):
            await Atomic(S.f0.set(i)).execute(ctx)
    return results[0]


async def bench_10_field_write_separate_atomic(ctx: Context, n: int) -> TimingResult:
    """Write 10 fields, each in separate Atomic (simulates auto_atomic per-term)."""
    # Warm up
    await Atomic(S.f0.set(0)).execute(ctx)
    get_counters().reset()

    with timed_run(f"10_fields_separate_atomic x{n}", n) as results:
        for i in range(n):
            await Atomic(S.f0.set(i)).execute(ctx)
            await Atomic(S.f1.set(i)).execute(ctx)
            await Atomic(S.f2.set(f"val_{i}")).execute(ctx)
            await Atomic(S.f3.set(float(i))).execute(ctx)
            await Atomic(S.f4.set(i % 2 == 0)).execute(ctx)
            await Atomic(S.f5.set(i * 10)).execute(ctx)
            await Atomic(S.f6.set(f"str_{i}")).execute(ctx)
            await Atomic(S.f7.set(float(i) * 0.5)).execute(ctx)
            await Atomic(S.f8.set(i + 100)).execute(ctx)
            await Atomic(S.f9.set(f"end_{i}")).execute(ctx)
    return results[0]


async def bench_10_field_write_single_atomic(ctx: Context, n: int) -> TimingResult:
    """Write 10 fields in a single Atomic (batched transaction)."""
    # Warm up
    await Atomic(S.f0.set(0)).execute(ctx)
    get_counters().reset()

    with timed_run(f"10_fields_single_atomic x{n}", n) as results:
        for i in range(n):
            await Atomic(
                Seq(
                    S.f0.set(i),
                    S.f1.set(i),
                    S.f2.set(f"val_{i}"),
                    S.f3.set(float(i)),
                    S.f4.set(i % 2 == 0),
                    S.f5.set(i * 10),
                    S.f6.set(f"str_{i}"),
                    S.f7.set(float(i) * 0.5),
                    S.f8.set(i + 100),
                    S.f9.set(f"end_{i}"),
                ),
            ).execute(ctx)
    return results[0]


async def bench_auto_atomic_10_fields(ctx: Context, n: int) -> TimingResult:
    """Write 10 fields via auto_atomic (wraps each term individually)."""
    # Warm up
    await Atomic(S.f0.set(0)).execute(ctx)
    get_counters().reset()

    with timed_run(f"10_fields_auto_atomic x{n}", n) as results:
        for i in range(n):
            tree = Seq(
                S.f0.set(i),
                S.f1.set(i),
                S.f2.set(f"val_{i}"),
                S.f3.set(float(i)),
                S.f4.set(i % 2 == 0),
                S.f5.set(i * 10),
                S.f6.set(f"str_{i}"),
                S.f7.set(float(i) * 0.5),
                S.f8.set(i + 100),
                S.f9.set(f"end_{i}"),
            )
            tree = auto_atomic(tree)
            await tree.execute(ctx)
    return results[0]


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------

N = 100


async def run_all() -> list[TimingResult]:
    install_counters()
    results = []

    import shutil
    import tempfile

    from everypv.adapters.storage import rocksdb_storage_inmemory

    tmpdir = tempfile.mkdtemp(prefix="bench_flat_")
    try:
        with rocksdb_storage_inmemory(tmpdir) as storage:
            ctx = Context().with_handle(StorageProtocol, storage)

            results.append(await bench_single_field_write(ctx, N))
            results.append(await bench_10_field_write_separate_atomic(ctx, N))
            results.append(await bench_10_field_write_single_atomic(ctx, N))
            results.append(await bench_auto_atomic_10_fields(ctx, N))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    uninstall_counters()
    print_results("Scenario 1: Flat Writes", results)
    return results


if __name__ == "__main__":
    asyncio.run(run_all())
