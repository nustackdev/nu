"""Scenario 3: Dict-of-Shapes CRUD — create, read, update, delete.

Measures: dict_view.store, container creation for dynamic entries, scan/iteration.
Varies: number of entries (10, 100, 500), fields per sub-shape.
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
from everypv import Atomic
from everyshape import Shape


# --------------------------------------------------------------------------
# Shapes
# --------------------------------------------------------------------------


class Product(Shape):
    name = pv.StrRef.slot()
    price = pv.FloatRef.slot()
    stock = pv.IntRef.slot()


class Catalog(Shape):
    products = pv.ShapesDictRef.slot(shape_type=Product)


# --------------------------------------------------------------------------
# Benchmarks
# --------------------------------------------------------------------------


async def bench_create_entries(ctx: Context, n: int) -> TimingResult:
    """Create N shape entries in a ShapesDictRef, each in its own Atomic."""
    get_counters().reset()

    with timed_run(f"create_{n}_entries", n) as results:
        for i in range(n):
            await Atomic(
                Catalog.products[f"item_{i}"].store(
                    {
                        "name": f"Product {i}",
                        "price": float(i) * 1.5,
                        "stock": i * 10,
                    }
                ),
            ).execute(ctx)
    return results[0]


async def bench_create_entries_batched(ctx: Context, n: int) -> TimingResult:
    """Create N shape entries in a single Atomic."""
    get_counters().reset()

    children = []
    for i in range(n):
        children.append(
            Catalog.products[f"batch_{i}"].store(
                {
                    "name": f"Product {i}",
                    "price": float(i) * 1.5,
                    "stock": i * 10,
                }
            ),
        )

    with timed_run(f"create_{n}_entries_batched", n) as results:
        await Atomic(Seq(*children)).execute(ctx)
    return results[0]


async def bench_read_fields(ctx: Context, n: int) -> TimingResult:
    """Read 3 fields from N existing entries (each read in own Atomic)."""
    # Ensure entries exist
    for i in range(n):
        await Atomic(
            Catalog.products[f"read_{i}"].store(
                {
                    "name": f"P{i}",
                    "price": float(i),
                    "stock": i,
                }
            ),
        ).execute(ctx)
    get_counters().reset()

    with timed_run(f"read_{n}_entries_fields", n) as results:
        for i in range(n):
            key = f"read_{i}"
            await Atomic(
                Seq(
                    Catalog.products[key].name.get(),
                    Catalog.products[key].price.get(),
                    Catalog.products[key].stock.get(),
                ),
            ).execute(ctx)
    return results[0]


async def bench_update_field(ctx: Context, n: int) -> TimingResult:
    """Update a single field on N existing entries."""
    # Ensure entries exist
    for i in range(n):
        await Atomic(
            Catalog.products[f"upd_{i}"].store(
                {
                    "name": f"P{i}",
                    "price": float(i),
                    "stock": i,
                }
            ),
        ).execute(ctx)
    get_counters().reset()

    with timed_run(f"update_{n}_entries_1field", n) as results:
        for i in range(n):
            await Atomic(
                Catalog.products[f"upd_{i}"].stock.set(i * 100),
            ).execute(ctx)
    return results[0]


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------


async def run_all() -> list[TimingResult]:
    install_counters()
    results = []

    for n in [10, 100, 500]:
        tmpdir = tempfile.mkdtemp(prefix="bench_dict_")
        try:
            from everypv.adapters.storage import rocksdb_storage_inmemory

            with rocksdb_storage_inmemory(tmpdir) as storage:
                ctx = Context().with_handle(StorageProtocol, storage)

                results.append(await bench_create_entries(ctx, n))
                results.append(await bench_create_entries_batched(ctx, n))
                results.append(await bench_read_fields(ctx, n))
                results.append(await bench_update_field(ctx, n))
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    uninstall_counters()
    print_results("Scenario 3: Dict-of-Shapes CRUD", results)
    return results


if __name__ == "__main__":
    asyncio.run(run_all())
