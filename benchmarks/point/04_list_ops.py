"""Scenario 4: List Append & Iteration — ListRef operations.

Measures: list_view.store/append, iter_children, extraction overhead.
Varies: list size (10, 100, 500), item complexity (int vs string).
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


# --------------------------------------------------------------------------
# Shapes
# --------------------------------------------------------------------------


class ListBench(Shape):
    ints = pv.ListRef.slot(item_type=int)
    strs = pv.ListRef.slot(item_type=str)


# --------------------------------------------------------------------------
# Benchmarks
# --------------------------------------------------------------------------


async def bench_store_list(ctx: Context, n: int) -> TimingResult:
    """Store a list of N ints in one shot."""
    data = list(range(n))
    get_counters().reset()

    with timed_run(f"store_list_int_{n}", 1) as results:
        await Atomic(ListBench.ints.store(data)).execute(ctx)
    return results[0]


async def bench_store_list_str(ctx: Context, n: int) -> TimingResult:
    """Store a list of N strings in one shot."""
    data = [f"item_{i}" for i in range(n)]
    get_counters().reset()

    with timed_run(f"store_list_str_{n}", 1) as results:
        await Atomic(ListBench.strs.store(data)).execute(ctx)
    return results[0]


async def bench_read_list(ctx: Context, n: int) -> TimingResult:
    """Read back entire list of N ints."""
    data = list(range(n))
    await Atomic(ListBench.ints.store(data)).execute(ctx)
    get_counters().reset()

    with timed_run(f"read_list_int_{n}", 1) as results:
        await Atomic(ListBench.ints.get()).execute(ctx)
    return results[0]


async def bench_read_by_index(ctx: Context, n: int) -> TimingResult:
    """Read N individual elements by index."""
    data = list(range(n))
    await Atomic(ListBench.ints.store(data)).execute(ctx)
    get_counters().reset()

    with timed_run(f"read_by_index_{n}", n) as results:
        for i in range(n):
            await Atomic(ListBench.ints[i].get()).execute(ctx)
    return results[0]


async def bench_append_one_by_one(ctx: Context, n: int) -> TimingResult:
    """Append N items one by one, each in its own Atomic."""
    await Atomic(ListBench.ints.store([])).execute(ctx)
    get_counters().reset()

    with timed_run(f"append_one_by_one_{n}", n) as results:
        for i in range(n):
            await Atomic(ListBench.ints.append(i)).execute(ctx)
    return results[0]


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------


async def run_all() -> list[TimingResult]:
    install_counters()
    results = []

    for n in [10, 100, 500]:
        tmpdir = tempfile.mkdtemp(prefix="bench_list_")
        try:
            from everypv.adapters.storage import rocksdb_storage_inmemory

            with rocksdb_storage_inmemory(tmpdir) as storage:
                ctx = Context().with_handle(StorageProtocol, storage)

                results.append(await bench_store_list(ctx, n))
                results.append(await bench_store_list_str(ctx, n))
                results.append(await bench_read_list(ctx, n))
                results.append(await bench_read_by_index(ctx, n))
                results.append(await bench_append_one_by_one(ctx, n))
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    uninstall_counters()
    print_results("Scenario 4: List Append & Iteration", results)
    return results


if __name__ == "__main__":
    asyncio.run(run_all())
