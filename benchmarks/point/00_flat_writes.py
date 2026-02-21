"""Flat Writes -- pure write throughput for primitive fields.

Measures: Atomic execution overhead for flat shape field writes.
Compares: single-field, 10-field separate Atomic, single Atomic, auto_atomic.

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


# ── Pre-built terms ──────────────────────────────────────────────────

TERM_SINGLE = Atomic(S.f0.set(42))

TERMS_10_SEPARATE = [
    Atomic(S.f0.set(1)),
    Atomic(S.f1.set(2)),
    Atomic(S.f2.set("val")),
    Atomic(S.f3.set(3.14)),
    Atomic(S.f4.set(True)),
    Atomic(S.f5.set(10)),
    Atomic(S.f6.set("str")),
    Atomic(S.f7.set(0.5)),
    Atomic(S.f8.set(100)),
    Atomic(S.f9.set("end")),
]

TERM_10_SINGLE = Atomic(
    Seq(
        S.f0.set(1),
        S.f1.set(2),
        S.f2.set("val"),
        S.f3.set(3.14),
        S.f4.set(True),
        S.f5.set(10),
        S.f6.set("str"),
        S.f7.set(0.5),
        S.f8.set(100),
        S.f9.set("end"),
    ),
)

TERM_10_AUTO = auto_atomic(
    Seq(
        S.f0.set(1),
        S.f1.set(2),
        S.f2.set("val"),
        S.f3.set(3.14),
        S.f4.set(True),
        S.f5.set(10),
        S.f6.set("str"),
        S.f7.set(0.5),
        S.f8.set(100),
        S.f9.set("end"),
    ),
)


# ── Benchmarks ───────────────────────────────────────────────────────

N = 100


async def bench_single_field_write(ctx: Context) -> TimingResult:
    """Write a single int field N times (pre-built Atomic)."""
    await TERM_SINGLE.execute(ctx)  # warm up
    get_counters().reset()

    with timed_run(f"single_field x{N}", N) as results:
        for _ in range(N):
            await TERM_SINGLE.execute(ctx)
    return results[0]


async def bench_10_field_write_separate_atomic(ctx: Context) -> TimingResult:
    """Write 10 fields, each in separate pre-built Atomic."""
    await TERM_SINGLE.execute(ctx)  # warm up
    get_counters().reset()

    with timed_run(f"10_fields_separate_atomic x{N}", N) as results:
        for _ in range(N):
            for term in TERMS_10_SEPARATE:
                await term.execute(ctx)
    return results[0]


async def bench_10_field_write_single_atomic(ctx: Context) -> TimingResult:
    """Write 10 fields in a single pre-built Atomic (batched transaction)."""
    await TERM_SINGLE.execute(ctx)  # warm up
    get_counters().reset()

    with timed_run(f"10_fields_single_atomic x{N}", N) as results:
        for _ in range(N):
            await TERM_10_SINGLE.execute(ctx)
    return results[0]


async def bench_auto_atomic_10_fields(ctx: Context) -> TimingResult:
    """Write 10 fields via pre-built auto_atomic tree."""
    await TERM_SINGLE.execute(ctx)  # warm up
    get_counters().reset()

    with timed_run(f"10_fields_auto_atomic x{N}", N) as results:
        for _ in range(N):
            await TERM_10_AUTO.execute(ctx)
    return results[0]


# ── Runner ───────────────────────────────────────────────────────────


async def run_all() -> list[TimingResult]:
    install_counters()
    results = []

    tmpdir = tempfile.mkdtemp(prefix="bench_flat_")
    try:
        from everypv.adapters.storage import rocksdb_storage_inmemory

        with rocksdb_storage_inmemory(tmpdir) as storage:
            ctx = Context().with_handle(StorageProtocol, storage)

            results.append(await bench_single_field_write(ctx))
            results.append(await bench_10_field_write_separate_atomic(ctx))
            results.append(await bench_10_field_write_single_atomic(ctx))
            results.append(await bench_auto_atomic_10_fields(ctx))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    uninstall_counters()
    print_results("Flat Writes", results)
    return results


if __name__ == "__main__":
    asyncio.run(run_all())
