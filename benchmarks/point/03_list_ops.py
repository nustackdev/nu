"""List Append & Iteration -- ListRef operations.

Measures: list store/read/append/index-read at sizes 10/100/500.
All term trees are pre-built per N. Benchmark loops measure only execution.
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
from eb_virtuals import Atomic
from everybase import Context
from everybase.shape import Shape


# ── Shapes ────────────────────────────────────────────────────────────


class ListBench(Shape):
    ints = ebv.ListRef.slot(item_type=int)
    strs = ebv.ListRef.slot(item_type=str)


# ── Pre-built terms (per N) ──────────────────────────────────────────


def _build_terms(n: int) -> dict:
    """Build all term trees for a given list size."""
    int_data = list(range(n))
    str_data = [f"item_{i}" for i in range(n)]

    return {
        "store_int": Atomic(ListBench.ints.store(int_data)),
        "store_str": Atomic(ListBench.strs.store(str_data)),
        "read_int": Atomic(ListBench.ints),
        "read_by_index": [Atomic(ListBench.ints[i]) for i in range(n)],
        "append": [Atomic(ListBench.ints.append(i)) for i in range(n)],
        "clear": Atomic(ListBench.ints.store([])),
    }


# ── Benchmarks ───────────────────────────────────────────────────────


async def bench_store_list(ctx: Context, n: int, terms: dict) -> TimingResult:
    """Store a list of N ints in one shot (pre-built Atomic)."""
    get_counters().reset()

    with timed_run(f"store_list_int_{n}", 1) as results:
        await terms["store_int"].execute(ctx)
    return results[0]


async def bench_store_list_str(ctx: Context, n: int, terms: dict) -> TimingResult:
    """Store a list of N strings in one shot (pre-built Atomic)."""
    get_counters().reset()

    with timed_run(f"store_list_str_{n}", 1) as results:
        await terms["store_str"].execute(ctx)
    return results[0]


async def bench_read_list(ctx: Context, n: int, terms: dict) -> TimingResult:
    """Read back entire list of N ints (pre-built Atomic)."""
    await terms["store_int"].execute(ctx)
    get_counters().reset()

    with timed_run(f"read_list_int_{n}", 1) as results:
        await terms["read_int"].execute(ctx)
    return results[0]


async def bench_read_by_index(ctx: Context, n: int, terms: dict) -> TimingResult:
    """Read N individual elements by index (pre-built Atomics)."""
    await terms["store_int"].execute(ctx)
    get_counters().reset()

    with timed_run(f"read_by_index_{n}", n) as results:
        for term in terms["read_by_index"]:
            await term.execute(ctx)
    return results[0]


async def bench_append_one_by_one(ctx: Context, n: int, terms: dict) -> TimingResult:
    """Append N items one by one (pre-built Atomics)."""
    await terms["clear"].execute(ctx)
    get_counters().reset()

    with timed_run(f"append_one_by_one_{n}", n) as results:
        for term in terms["append"]:
            await term.execute(ctx)
    return results[0]


# ── Runner ───────────────────────────────────────────────────────────


async def run_all() -> list[TimingResult]:
    install_counters()
    results = []

    for n in [10, 100, 500]:
        terms = _build_terms(n)
        tmpdir = tempfile.mkdtemp(prefix="bench_list_")
        try:
            from eb_virtuals.presets import rocksdb_storage_inmemory

            with rocksdb_storage_inmemory(tmpdir) as storage:
                ctx = Context().bind(storage, StorageProtocol)

                results.append(await bench_store_list(ctx, n, terms))
                results.append(await bench_store_list_str(ctx, n, terms))
                results.append(await bench_read_list(ctx, n, terms))
                results.append(await bench_read_by_index(ctx, n, terms))
                results.append(await bench_append_one_by_one(ctx, n, terms))
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    uninstall_counters()
    print_results("List Ops", results)
    return results


if __name__ == "__main__":
    asyncio.run(run_all())
