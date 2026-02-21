"""Scenario: Market Catalog -- 5 categories x 10 products x 4 fields.

Real-world pattern: nested shapes, compound .store(), pre-built trees.
Trees are built once outside the timed section. Only .execute(ctx) is measured.

Two atomicity modes:
  auto_atomic -- each Term wrapped in its own Atomic (1 txn per field op)
  Atomic      -- single Atomic wrapping entire Seq (1 txn for all ops)

Benchmarks (x2 modes):
  store  -- populate entire catalog (200+ values)
  read   -- read all product fields (200 reads)
  update -- update all prices (50 writes)
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

# Raw Seq (unwrapped) -- shared base for both modes
_store_seq = Seq(
    *[Catalog.categories[cat_key].store(cat_data) for cat_key, cat_data in CATEGORIES.items()]
)

_read_seq = Seq(
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

_update_seq = Seq(
    *[
        Catalog.categories[cat_key].products[prod_key].price.set(0.99)
        for cat_key, cat_data in CATEGORIES.items()
        for prod_key in cat_data["products"]
    ]
)

# auto_atomic: each Term gets its own Atomic (1 txn per field op)
store_tree_aa = auto_atomic(_store_seq)
read_tree_aa = auto_atomic(_read_seq)
update_tree_aa = auto_atomic(_update_seq)

# Atomic: single txn wrapping entire Seq
store_tree_at = Atomic(_store_seq)
read_tree_at = Atomic(_read_seq)
update_tree_at = Atomic(_update_seq)


# ── Benchmarks ────────────────────────────────────────────────────────────────

N = 200  # iterations


async def _bench(label: str, tree, seed_tree) -> TimingResult:
    """Benchmark with fresh db: seed once, then time tree N times."""
    tmpdir = tempfile.mkdtemp(prefix="bench_market_")
    try:
        from everypv.adapters.storage import rocksdb_storage_inmemory

        with rocksdb_storage_inmemory(tmpdir) as storage:
            ctx = Context().with_handle(StorageProtocol, storage)
            await seed_tree.execute(ctx)
            get_counters().reset()

            with timed_run(label, N) as results:
                for _ in range(N):
                    await tree.execute(ctx)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


# ── Runner ────────────────────────────────────────────────────────────────────


async def run_all() -> list[TimingResult]:
    install_counters()
    results = []

    # auto_atomic (1 txn per field op)
    results.append(await _bench(f"store auto_atomic x{N}", store_tree_aa, store_tree_aa))
    results.append(await _bench(f"read auto_atomic x{N}", read_tree_aa, store_tree_aa))
    results.append(await _bench(f"update auto_atomic x{N}", update_tree_aa, store_tree_aa))

    # Atomic (1 txn for all ops)
    results.append(await _bench(f"store Atomic x{N}", store_tree_at, store_tree_at))
    results.append(await _bench(f"read Atomic x{N}", read_tree_at, store_tree_at))
    results.append(await _bench(f"update Atomic x{N}", update_tree_at, store_tree_at))

    uninstall_counters()
    print_results("Scenario: Market Catalog", results)
    return results


if __name__ == "__main__":
    asyncio.run(run_all())
