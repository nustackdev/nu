"""Scenario 6: Auto-Atomic Granularity — transaction boundary overhead.

Compares: per-Term auto_atomic vs manual coarse Atomic vs no Atomic (raw DictView).
Isolates: transaction boundaries, scope detection (find()), span enter/exit.
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
from everypv.views import DictView
from everyshape import Shape


# --------------------------------------------------------------------------
# Shapes
# --------------------------------------------------------------------------


class BenchShape(Shape):
    f0 = pv.IntRef.slot()
    f1 = pv.IntRef.slot()
    f2 = pv.StrRef.slot()
    f3 = pv.FloatRef.slot()
    f4 = pv.IntRef.slot()


S = BenchShape

FIELDS_PER_OP = 5


def make_writes(i: int) -> list:
    return [
        S.f0.set(i),
        S.f1.set(i * 2),
        S.f2.set(f"v{i}"),
        S.f3.set(float(i) * 0.1),
        S.f4.set(i + 100),
    ]


# --------------------------------------------------------------------------
# Benchmarks
# --------------------------------------------------------------------------


async def bench_auto_atomic_per_term(ctx: Context, n: int) -> TimingResult:
    """auto_atomic wraps each Term individually (current default behavior)."""
    # Warm up
    tree = auto_atomic(Seq(*make_writes(0)))
    await tree.execute(ctx)
    get_counters().reset()

    with timed_run(f"auto_atomic_per_term x{n}", n) as results:
        for i in range(n):
            tree = Seq(*make_writes(i))
            tree = auto_atomic(tree)
            await tree.execute(ctx)
    return results[0]


async def bench_single_atomic(ctx: Context, n: int) -> TimingResult:
    """Single manual Atomic wrapping all writes (one transaction per op)."""
    await Atomic(Seq(*make_writes(0))).execute(ctx)
    get_counters().reset()

    with timed_run(f"single_atomic x{n}", n) as results:
        for i in range(n):
            await Atomic(Seq(*make_writes(i))).execute(ctx)
    return results[0]


async def bench_raw_dictview(storage: object, n: int) -> TimingResult:
    """Raw DictView operations — no term tree, no Atomic, direct storage calls."""
    get_counters().reset()

    with timed_run(f"raw_dictview x{n}", n) as results:
        for i in range(n):
            with storage.transaction() as tx:  # type: ignore[union-attr]
                root = DictView.open_root(tx)
                root["f0"] = i
                root["f1"] = i * 2
                root["f2"] = f"v{i}"
                root["f3"] = float(i) * 0.1
                root["f4"] = i + 100
    return results[0]


async def bench_batched_auto_atomic(ctx: Context, n: int, batch_size: int) -> TimingResult:
    """Batch multiple ops into a single Atomic, then auto_atomic the batch."""
    await Atomic(Seq(*make_writes(0))).execute(ctx)
    get_counters().reset()

    full_batches = n // batch_size
    remainder = n % batch_size

    with timed_run(f"batched_auto_atomic_bs{batch_size} x{n}", n) as results:
        for b in range(full_batches):
            children = []
            for j in range(batch_size):
                i = b * batch_size + j
                children.extend(make_writes(i))
            await Atomic(Seq(*children)).execute(ctx)

        if remainder:
            children = []
            for j in range(remainder):
                i = full_batches * batch_size + j
                children.extend(make_writes(i))
            await Atomic(Seq(*children)).execute(ctx)
    return results[0]


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------

N = 200


async def run_all() -> list[TimingResult]:
    install_counters()
    results = []

    tmpdir = tempfile.mkdtemp(prefix="bench_atomic_")
    try:
        from everypv.adapters.storage import rocksdb_storage_inmemory

        with rocksdb_storage_inmemory(tmpdir) as storage:
            ctx = Context().with_handle(StorageProtocol, storage)

            results.append(await bench_auto_atomic_per_term(ctx, N))
            results.append(await bench_single_atomic(ctx, N))
            results.append(await bench_raw_dictview(storage, N))
            results.append(await bench_batched_auto_atomic(ctx, N, 10))
            results.append(await bench_batched_auto_atomic(ctx, N, 50))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    uninstall_counters()
    print_results("Scenario 6: Auto-Atomic Granularity", results)
    return results


if __name__ == "__main__":
    asyncio.run(run_all())
