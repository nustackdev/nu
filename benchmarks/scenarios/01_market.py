"""Scenario: Market Catalog -- 5 categories x 10 products x 4 fields.

Real-world pattern: nested shapes, compound .store(), pre-built trees.
Trees are built once outside the timed section. Only .execute(ctx) is measured.

Benchmarks:
  store  -- populate entire catalog (200+ values) via auto_atomic
  read   -- read all product fields via auto_atomic
  update -- update all prices via auto_atomic
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
from everypv import auto_atomic
from everyshape import Shape


# ── Shapes ────────────────────────────────────────────────────────────────────


class Product(Shape):
    name = pv.StrRef.slot()
    price = pv.FloatRef.slot()
    stock = pv.IntRef.slot()
    rating = pv.FloatRef.slot()


class Category(Shape):
    label = pv.StrRef.slot()
    products = pv.ShapesDictRef.slot(shape_type=Product)


class Catalog(Shape):
    categories = pv.ShapesDictRef.slot(shape_type=Category)


# ── Data ──────────────────────────────────────────────────────────────────────

NUM_CATEGORIES = 5
NUM_PRODUCTS = 10

CATEGORIES = {
    f"cat_{c}": {
        "label": f"Category {c}",
        "products": {
            f"prod_{p}": {
                "name": f"Product {c}-{p}",
                "price": float(c * 10 + p) * 1.99,
                "stock": (c + 1) * (p + 1) * 5,
                "rating": round(3.0 + (c + p) * 0.1, 1),
            }
            for p in range(NUM_PRODUCTS)
        },
    }
    for c in range(NUM_CATEGORIES)
}


# ── Trees (built once) ───────────────────────────────────────────────────────

store_tree = auto_atomic(
    Seq(*[Catalog.categories[cat_key].store(cat_data) for cat_key, cat_data in CATEGORIES.items()])
)

read_tree = auto_atomic(
    Seq(
        *[
            term
            for cat_key, cat_data in CATEGORIES.items()
            for prod_key in cat_data["products"]
            for term in (
                Catalog.categories[cat_key].products[prod_key].name.get(),
                Catalog.categories[cat_key].products[prod_key].price.get(),
                Catalog.categories[cat_key].products[prod_key].stock.get(),
                Catalog.categories[cat_key].products[prod_key].rating.get(),
            )
        ]
    )
)

update_tree = auto_atomic(
    Seq(
        *[
            Catalog.categories[cat_key].products[prod_key].price.set(0.99)
            for cat_key, cat_data in CATEGORIES.items()
            for prod_key in cat_data["products"]
        ]
    )
)


# ── Benchmarks ────────────────────────────────────────────────────────────────

N = 50  # iterations (heavier trees, fewer reps)


async def bench_store(ctx: Context) -> TimingResult:
    """Store entire catalog (200+ values) via auto_atomic, N times."""
    # Warm up
    await store_tree.execute(ctx)
    get_counters().reset()

    with timed_run(f"market store 5x10x4 x{N}", N) as results:
        for _ in range(N):
            await store_tree.execute(ctx)
    return results[0]


async def bench_read(ctx: Context) -> TimingResult:
    """Read all product fields (200) via auto_atomic, N times."""
    await store_tree.execute(ctx)
    get_counters().reset()

    with timed_run(f"market read 50x4 x{N}", N) as results:
        for _ in range(N):
            await read_tree.execute(ctx)
    return results[0]


async def bench_update(ctx: Context) -> TimingResult:
    """Update all 50 prices via auto_atomic, N times."""
    await store_tree.execute(ctx)
    get_counters().reset()

    with timed_run(f"market update 50x1 x{N}", N) as results:
        for _ in range(N):
            await update_tree.execute(ctx)
    return results[0]


# ── Runner ────────────────────────────────────────────────────────────────────


async def run_all() -> list[TimingResult]:
    install_counters()
    results = []

    tmpdir = tempfile.mkdtemp(prefix="bench_market_")
    try:
        from everypv.adapters.storage import rocksdb_storage_inmemory

        with rocksdb_storage_inmemory(tmpdir) as storage:
            ctx = Context().with_handle(StorageProtocol, storage)

            results.append(await bench_store(ctx))
            results.append(await bench_read(ctx))
            results.append(await bench_update(ctx))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    uninstall_counters()
    print_results("Scenario: Market Catalog", results)
    return results


if __name__ == "__main__":
    asyncio.run(run_all())
