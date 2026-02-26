"""Dict-of-Shapes CRUD -- create, read, update.

Measures: ShapesDictRef store, field read, field update at 10/100/500 entries.
All term trees are pre-built per N. Benchmark loops measure only execution.
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


# ── Shapes ────────────────────────────────────────────────────────────


class Product(Shape):
    name = pv.StrRef.slot()
    price = pv.FloatRef.slot()
    stock = pv.IntRef.slot()


class Catalog(Shape):
    products = pv.ShapesDictRef.slot(shape_type=Product)


# ── Pre-built terms (per N) ──────────────────────────────────────────


def _build_terms(n: int) -> dict:
    """Build all term trees for a given entry count."""
    keys = [f"item_{i}" for i in range(n)]
    data = {"name": "Product", "price": 9.99, "stock": 100}

    # Create: one Atomic per entry
    create_terms = [Atomic(Catalog.products[k].set(data)) for k in keys]

    # Create batched: all entries in single Atomic
    create_batched = Atomic(Seq(*[Catalog.products[k].set(data) for k in keys]))

    # Seed: populate for read/update benchmarks
    seed = Atomic(Seq(*[Catalog.products[f"s_{k}"].set(data) for k in keys]))
    seed_keys = [f"s_{k}" for k in keys]

    # Read: 3 fields per entry in single Atomic
    read_terms = [
        Atomic(
            Seq(
                Catalog.products[k].name.get(),
                Catalog.products[k].price.get(),
                Catalog.products[k].stock.get(),
            ),
        )
        for k in seed_keys
    ]

    # Update: single field per entry
    update_terms = [Atomic(Catalog.products[k].stock.set(999)) for k in seed_keys]

    return {
        "create": create_terms,
        "create_batched": create_batched,
        "seed": seed,
        "read": read_terms,
        "update": update_terms,
    }


# ── Benchmarks ───────────────────────────────────────────────────────


async def bench_create_entries(ctx: Context, n: int, terms: dict) -> TimingResult:
    """Create N shape entries, each in its own pre-built Atomic."""
    get_counters().reset()

    with timed_run(f"create_{n}_entries", n) as results:
        for term in terms["create"]:
            await term.execute(ctx)
    return results[0]


async def bench_create_entries_batched(ctx: Context, n: int, terms: dict) -> TimingResult:
    """Create N shape entries in a single pre-built Atomic."""
    get_counters().reset()

    with timed_run(f"create_{n}_entries_batched", n) as results:
        await terms["create_batched"].execute(ctx)
    return results[0]


async def bench_read_fields(ctx: Context, n: int, terms: dict) -> TimingResult:
    """Read 3 fields from N existing entries (pre-built Atomics)."""
    await terms["seed"].execute(ctx)
    get_counters().reset()

    with timed_run(f"read_{n}_entries_fields", n) as results:
        for term in terms["read"]:
            await term.execute(ctx)
    return results[0]


async def bench_update_field(ctx: Context, n: int, terms: dict) -> TimingResult:
    """Update a single field on N existing entries (pre-built Atomics)."""
    await terms["seed"].execute(ctx)
    get_counters().reset()

    with timed_run(f"update_{n}_entries_1field", n) as results:
        for term in terms["update"]:
            await term.execute(ctx)
    return results[0]


# ── Runner ───────────────────────────────────────────────────────────


async def run_all() -> list[TimingResult]:
    install_counters()
    results = []

    for n in [10, 100, 500]:
        terms = _build_terms(n)
        tmpdir = tempfile.mkdtemp(prefix="bench_dict_")
        try:
            from everypv.adapters.storage import rocksdb_storage_inmemory

            with rocksdb_storage_inmemory(tmpdir) as storage:
                ctx = Context().bind(storage, StorageProtocol)

                results.append(await bench_create_entries(ctx, n, terms))
                results.append(await bench_create_entries_batched(ctx, n, terms))
                results.append(await bench_read_fields(ctx, n, terms))
                results.append(await bench_update_field(ctx, n, terms))
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    uninstall_counters()
    print_results("Dict-of-Shapes CRUD", results)
    return results


if __name__ == "__main__":
    asyncio.run(run_all())
