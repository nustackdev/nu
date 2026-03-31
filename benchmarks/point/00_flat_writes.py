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

from utils import (
    TimingResult,
    get_counters,
    install_counters,
    print_results,
    timed_run,
    uninstall_counters,
)
from virtuals.tkv.storage import StorageProtocol

import nu_virtuals as ebv
from nu_virtuals import Atomic, auto_atomic
from nu import Context
from nu.abc import Seq
from nu.shape import Shape


# ── Shapes ────────────────────────────────────────────────────────────


class FlatShape(Shape):
    f0 = ebv.IntRef.slot()
    f1 = ebv.IntRef.slot()
    f2 = ebv.StrRef.slot()
    f3 = ebv.FloatRef.slot()
    f4 = ebv.BoolRef.slot()
    f5 = ebv.IntRef.slot()
    f6 = ebv.StrRef.slot()
    f7 = ebv.FloatRef.slot()
    f8 = ebv.IntRef.slot()
    f9 = ebv.StrRef.slot()


S = FlatShape


# ── Pre-built terms ──────────────────────────────────────────────────

TERM_SINGLE = Atomic(S.f0.store(42))

TERMS_10_SEPARATE = [
    Atomic(S.f0.store(1)),
    Atomic(S.f1.store(2)),
    Atomic(S.f2.store("val")),
    Atomic(S.f3.store(3.14)),
    Atomic(S.f4.store(True)),
    Atomic(S.f5.store(10)),
    Atomic(S.f6.store("str")),
    Atomic(S.f7.store(0.5)),
    Atomic(S.f8.store(100)),
    Atomic(S.f9.store("end")),
]

TERM_10_SINGLE = Atomic(
    Seq(
        S.f0.store(1),
        S.f1.store(2),
        S.f2.store("val"),
        S.f3.store(3.14),
        S.f4.store(True),
        S.f5.store(10),
        S.f6.store("str"),
        S.f7.store(0.5),
        S.f8.store(100),
        S.f9.store("end"),
    ),
)

TERM_10_AUTO = auto_atomic(
    Seq(
        S.f0.store(1),
        S.f1.store(2),
        S.f2.store("val"),
        S.f3.store(3.14),
        S.f4.store(True),
        S.f5.store(10),
        S.f6.store("str"),
        S.f7.store(0.5),
        S.f8.store(100),
        S.f9.store("end"),
    ),
)


# ── Benchmarks ───────────────────────────────────────────────────────

N = 100


async def _bench(label: str, loop_body) -> TimingResult:
    """Benchmark with fresh db per measurement."""
    tmpdir = tempfile.mkdtemp(prefix="bench_flat_")
    try:
        from nu_virtuals.presets import rocksdb_storage_inmemory

        with rocksdb_storage_inmemory(tmpdir) as storage:
            ctx = Context().bind(storage, StorageProtocol)
            await TERM_SINGLE.execute(ctx)  # warm up
            get_counters().reset()

            with timed_run(label, N) as results:
                for _ in range(N):
                    await loop_body(ctx)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


# ── Runner ───────────────────────────────────────────────────────────


async def _run_single_field(ctx: Context) -> None:
    await TERM_SINGLE.execute(ctx)


async def _run_10_separate(ctx: Context) -> None:
    for term in TERMS_10_SEPARATE:
        await term.execute(ctx)


async def _run_10_single(ctx: Context) -> None:
    await TERM_10_SINGLE.execute(ctx)


async def _run_10_auto(ctx: Context) -> None:
    await TERM_10_AUTO.execute(ctx)


async def run_all() -> list[TimingResult]:
    install_counters()
    results = []

    results.append(await _bench(f"single_field x{N}", _run_single_field))
    results.append(await _bench(f"10_fields_separate_atomic x{N}", _run_10_separate))
    results.append(await _bench(f"10_fields_single_atomic x{N}", _run_10_single))
    results.append(await _bench(f"10_fields_auto_atomic x{N}", _run_10_auto))

    uninstall_counters()
    print_results("Flat Writes", results)
    return results


if __name__ == "__main__":
    asyncio.run(run_all())
