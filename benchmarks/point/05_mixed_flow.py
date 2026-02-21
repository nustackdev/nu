"""Scenario 5: Mixed Read/Write Flow — realistic term tree execution.

Measures: full stack cost including term resolution, auto_atomic, observer notifications.
Simulates a real processing step: reads refs, computes via FuncCallOp, writes results.
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
from everybase.abc import FloatValue, FuncCallOp, IntValue, Seq
from everypv import Atomic, auto_atomic
from everyshape import Shape


# --------------------------------------------------------------------------
# Shapes
# --------------------------------------------------------------------------


class Metrics(Shape):
    count = pv.IntRef.slot()
    total = pv.FloatRef.slot()
    average = pv.FloatRef.slot()
    min_val = pv.FloatRef.slot()
    max_val = pv.FloatRef.slot()
    label = pv.StrRef.slot()


# --------------------------------------------------------------------------
# Helper functions for FuncCallOp
# --------------------------------------------------------------------------


def compute_average(total: float, count: int) -> float:
    if count == 0:
        return 0.0
    return total / count


def compute_min(current: float, new_val: float) -> float:
    return min(current, new_val)


def compute_max(current: float, new_val: float) -> float:
    return max(current, new_val)


def format_label(count: int, avg: float) -> str:
    return f"n={count} avg={avg:.2f}"


# --------------------------------------------------------------------------
# Benchmarks
# --------------------------------------------------------------------------


async def bench_mixed_manual_atomic(ctx: Context, n: int) -> TimingResult:
    """Mixed read/write: read 3 fields, compute, write 4 fields. Single Atomic per op."""
    # Seed initial values
    await Atomic(
        Seq(
            Metrics.count.set(0),
            Metrics.total.set(0.0),
            Metrics.average.set(0.0),
            Metrics.min_val.set(999999.0),
            Metrics.max_val.set(-999999.0),
            Metrics.label.set("init"),
        ),
    ).execute(ctx)
    get_counters().reset()

    with timed_run(f"mixed_manual_atomic x{n}", n) as results:
        for i in range(n):
            new_val = float(i) * 1.7
            new_count = IntValue(FuncCallOp(lambda c: c + 1, Metrics.count))
            new_total = FloatValue(FuncCallOp(lambda t, v: t + v, Metrics.total, new_val))
            new_avg = FloatValue(FuncCallOp(compute_average, new_total, new_count))
            new_min = FloatValue(FuncCallOp(compute_min, Metrics.min_val, new_val))
            new_max = FloatValue(FuncCallOp(compute_max, Metrics.max_val, new_val))
            new_label = FuncCallOp(format_label, new_count, new_avg)

            await Atomic(
                Seq(
                    Metrics.count.set(new_count),
                    Metrics.total.set(new_total),
                    Metrics.average.set(new_avg),
                    Metrics.min_val.set(new_min),
                    Metrics.max_val.set(new_max),
                    Metrics.label.set(new_label),
                ),
            ).execute(ctx)
    return results[0]


async def bench_mixed_auto_atomic(ctx: Context, n: int) -> TimingResult:
    """Same mixed flow but via auto_atomic (per-term wrapping)."""
    # Seed initial values
    await Atomic(
        Seq(
            Metrics.count.set(0),
            Metrics.total.set(0.0),
            Metrics.average.set(0.0),
            Metrics.min_val.set(999999.0),
            Metrics.max_val.set(-999999.0),
            Metrics.label.set("init"),
        ),
    ).execute(ctx)
    get_counters().reset()

    with timed_run(f"mixed_auto_atomic x{n}", n) as results:
        for i in range(n):
            new_val = float(i) * 1.7
            new_count = IntValue(FuncCallOp(lambda c: c + 1, Metrics.count))
            new_total = FloatValue(FuncCallOp(lambda t, v: t + v, Metrics.total, new_val))
            new_avg = FloatValue(FuncCallOp(compute_average, new_total, new_count))
            new_min = FloatValue(FuncCallOp(compute_min, Metrics.min_val, new_val))
            new_max = FloatValue(FuncCallOp(compute_max, Metrics.max_val, new_val))
            new_label = FuncCallOp(format_label, new_count, new_avg)

            tree = Seq(
                Metrics.count.set(new_count),
                Metrics.total.set(new_total),
                Metrics.average.set(new_avg),
                Metrics.min_val.set(new_min),
                Metrics.max_val.set(new_max),
                Metrics.label.set(new_label),
            )
            tree = auto_atomic(tree)
            await tree.execute(ctx)
    return results[0]


async def bench_read_heavy(ctx: Context, n: int) -> TimingResult:
    """Read-heavy: read 5 fields, compute 1, write 1. Single Atomic."""
    await Atomic(
        Seq(
            Metrics.count.set(100),
            Metrics.total.set(500.0),
            Metrics.average.set(5.0),
            Metrics.min_val.set(1.0),
            Metrics.max_val.set(10.0),
            Metrics.label.set("init"),
        ),
    ).execute(ctx)
    get_counters().reset()

    with timed_run(f"read_heavy x{n}", n) as results:
        for i in range(n):
            # Read 5, write 1
            new_label = FuncCallOp(
                format_label,
                Metrics.count,
                Metrics.average,
            )
            await Atomic(Metrics.label.set(new_label)).execute(ctx)
    return results[0]


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------

N = 100


async def run_all() -> list[TimingResult]:
    install_counters()
    results = []

    tmpdir = tempfile.mkdtemp(prefix="bench_mixed_")
    try:
        from everypv.adapters.storage import rocksdb_storage_inmemory

        with rocksdb_storage_inmemory(tmpdir) as storage:
            ctx = Context().with_handle(StorageProtocol, storage)

            results.append(await bench_mixed_manual_atomic(ctx, N))
            results.append(await bench_mixed_auto_atomic(ctx, N))
            results.append(await bench_read_heavy(ctx, N))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    uninstall_counters()
    print_results("Scenario 5: Mixed Read/Write Flow", results)
    return results


if __name__ == "__main__":
    asyncio.run(run_all())
