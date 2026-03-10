"""Scenario: Market Catalog -- 5 categories x 10 products x 4 fields.

Real-world pattern: nested shapes, compound .store(), pre-built trees.
Trees are built once outside the timed section. Only .execute(ctx) is measured.

Modes:
  PV auto_atomic  -- each Term wrapped in its own Atomic (1 txn per field op)
  PV Atomic       -- single Atomic wrapping entire Seq (1 txn for all ops)
  everydict       -- plain dict substrate (no storage, no views)
  everydict+inline -- everydict with inline_refs deformation applied

Benchmarks (x4 modes):
  store  -- populate entire catalog (200+ values)
  read   -- read all product fields (200 reads)
  update -- update all prices (50 writes)
"""

from __future__ import annotations

import asyncio
import shutil
import sys
import tempfile
import time


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

import eb_dict as ed
import eb_virtuals as ebv
from eb_dict.meta import inline_refs as dict_inline_refs
from eb_virtuals import Atomic, auto_atomic
from eb_virtuals.meta import inline_refs as v_inline_refs
from everybase import Context
from everybase.abc import Seq
from everybase.shape import Shape


# ── Shapes (PV substrate) ────────────────────────────────────────────────────


class Product(Shape):
    name = ebv.StrRef.slot()
    price = ebv.FloatRef.slot()
    stock = ebv.IntRef.slot()
    rating = ebv.FloatRef.slot()


class Category(Shape):
    label = ebv.StrRef.slot()
    products = ebv.ShapesDictRef.slot(shape_type=Product)


class Catalog(Shape):
    categories = ebv.ShapesDictRef.slot(shape_type=Category)


# ── Shapes (dict substrate) ──────────────────────────────────────────────────


class DProduct(Shape):
    name = ed.StrRef.slot()
    price = ed.FloatRef.slot()
    stock = ed.IntRef.slot()
    rating = ed.FloatRef.slot()


class DCategory(Shape):
    label = ed.StrRef.slot()
    products = ed.ShapesDictRef.slot(shape_type=DProduct)


class DCatalog(Shape):
    categories = ed.ShapesDictRef.slot(shape_type=DCategory)


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


# ── Pure Python dict (imperative baseline) ───────────────────────────────────


def py_store(data: dict) -> None:
    cats = data.setdefault("categories", {})
    for ck, cv in CATEGORIES.items():
        cat = cats.setdefault(ck, {})
        cat["label"] = cv["label"]
        prods = cat.setdefault("products", {})
        for pk, pv_ in cv["products"].items():
            prods[pk] = {**pv_}


def py_read(data: dict) -> None:
    cats = data["categories"]
    for ck, cv in CATEGORIES.items():
        prods = cats[ck]["products"]
        for pk in cv["products"]:
            p = prods[pk]
            _ = p["name"], p["price"], p["stock"], p["rating"]


def py_update(data: dict) -> None:
    cats = data["categories"]
    for ck, cv in CATEGORIES.items():
        prods = cats[ck]["products"]
        for pk in cv["products"]:
            prods[pk]["price"] = 0.99


def _bench_pure_dict(label: str, fn, setup_fn, field_ops: int) -> TimingResult:
    """Benchmark pure Python dict operations."""
    data: dict = {}
    setup_fn(data)  # seed
    # warmup
    fn(data)

    t0 = time.perf_counter()
    for _ in range(N):
        fn(data)
    elapsed = time.perf_counter() - t0

    return TimingResult(
        name=label,
        wall_time_s=elapsed,
        n_ops=N * field_ops,
        counters={},
    )


# ── Trees: PV (built once) ───────────────────────────────────────────────────

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
            Catalog.categories[cat_key].products[prod_key].name.load(),
            Catalog.categories[cat_key].products[prod_key].price.load(),
            Catalog.categories[cat_key].products[prod_key].stock.load(),
            Catalog.categories[cat_key].products[prod_key].rating.load(),
        )
    ]
)

_update_seq = Seq(
    *[
        Catalog.categories[cat_key].products[prod_key].price.store(0.99)
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

# Atomic + inline_refs
store_tree_ai = v_inline_refs(Atomic(_store_seq))
read_tree_ai = v_inline_refs(Atomic(_read_seq))
update_tree_ai = v_inline_refs(Atomic(_update_seq))


# ── Trees: everydict (built once) ───────────────────────────────────────────

_d_store_seq = Seq(
    *[
        term
        for cat_key, cat_data in CATEGORIES.items()
        for prod_key, prod_data in cat_data["products"].items()
        for term in (
            DCatalog.categories[cat_key].label.store(cat_data["label"]),
            DCatalog.categories[cat_key].products[prod_key].name.store(prod_data["name"]),
            DCatalog.categories[cat_key].products[prod_key].price.store(prod_data["price"]),
            DCatalog.categories[cat_key].products[prod_key].stock.store(prod_data["stock"]),
            DCatalog.categories[cat_key].products[prod_key].rating.store(prod_data["rating"]),
        )
    ]
)

_d_read_seq = Seq(
    *[
        term
        for cat_key, cat_data in CATEGORIES.items()
        for prod_key in cat_data["products"]
        for term in (
            DCatalog.categories[cat_key].products[prod_key].name.load(),
            DCatalog.categories[cat_key].products[prod_key].price.load(),
            DCatalog.categories[cat_key].products[prod_key].stock.load(),
            DCatalog.categories[cat_key].products[prod_key].rating.load(),
        )
    ]
)

_d_update_seq = Seq(
    *[
        DCatalog.categories[cat_key].products[prod_key].price.store(0.99)
        for cat_key, cat_data in CATEGORIES.items()
        for prod_key in cat_data["products"]
    ]
)

# everydict + inline_refs deformation
d_store_tree = _d_store_seq
d_read_tree = _d_read_seq
d_update_tree = _d_update_seq

di_store_tree = dict_inline_refs(_d_store_seq)
di_read_tree = dict_inline_refs(_d_read_seq)
di_update_tree = dict_inline_refs(_d_update_seq)


# ── Benchmarks ────────────────────────────────────────────────────────────────

N = 200  # iterations

# Field-level op counts per tree execution:
#   store: 5 cats x (1 label + 10 prods x 4 fields) = 255 writes
#   read:  5 cats x 10 prods x 4 fields = 200 reads
#   update: 5 cats x 10 prods x 1 price = 50 writes
FIELD_OPS = {"store": 255, "read": 200, "update": 50}


async def _bench_v(label: str, tree, seed_tree, field_ops: int) -> TimingResult:
    """Benchmark with fresh RocksDB: seed once, then time tree N times."""
    tmpdir = tempfile.mkdtemp(prefix="bench_market_")
    try:
        from eb_virtuals.presets import rocksdb_storage_inmemory

        with rocksdb_storage_inmemory(tmpdir) as storage:
            ctx = Context().bind(storage, StorageProtocol)
            await seed_tree.execute(ctx)
            get_counters().reset()

            with timed_run(label, N * field_ops) as results:
                for _ in range(N):
                    await tree.execute(ctx)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


async def _bench_dict(label: str, tree, seed_tree, field_ops: int) -> TimingResult:
    """Benchmark with fresh dict context: seed once, then time tree N times."""
    data: dict = {}
    ctx = Context().bind(data, dict, DCatalog)

    await seed_tree.execute(ctx)
    get_counters().reset()

    with timed_run(label, N * field_ops) as results:
        for _ in range(N):
            await tree.execute(ctx)
    return results[0]


# ── Runner ────────────────────────────────────────────────────────────────────


async def run_all() -> list[TimingResult]:
    install_counters()
    results = []

    s, r, u = FIELD_OPS["store"], FIELD_OPS["read"], FIELD_OPS["update"]

    # Pure Python dict (imperative baseline)
    results.append(_bench_pure_dict("store pure dict", py_store, py_store, s))
    results.append(_bench_pure_dict("read pure dict", py_read, py_store, r))
    results.append(_bench_pure_dict("update pure dict", py_update, py_store, u))

    # PV auto_atomic (1 txn per field op)
    results.append(await _bench_v("store virtuals auto_atomic", store_tree_aa, store_tree_aa, s))
    results.append(await _bench_v("read virtuals auto_atomic", read_tree_aa, store_tree_aa, r))
    results.append(await _bench_v("update virtuals auto_atomic", update_tree_aa, store_tree_aa, u))

    # PV Atomic (1 txn for all ops)
    results.append(await _bench_v("store virtuals Atomic", store_tree_at, store_tree_at, s))
    results.append(await _bench_v("read virtuals Atomic", read_tree_at, store_tree_at, r))
    results.append(await _bench_v("update virtuals Atomic", update_tree_at, store_tree_at, u))

    # PV Atomic + inline_refs
    results.append(await _bench_v("store virtuals Atomic+inline", store_tree_ai, store_tree_ai, s))
    results.append(await _bench_v("read virtuals Atomic+inline", read_tree_ai, store_tree_ai, r))
    results.append(
        await _bench_v("update virtuals Atomic+inline", update_tree_ai, store_tree_ai, u)
    )

    # everydict (no deformation)
    results.append(await _bench_dict("store everydict", d_store_tree, d_store_tree, s))
    results.append(await _bench_dict("read everydict", d_read_tree, d_store_tree, r))
    results.append(await _bench_dict("update everydict", d_update_tree, d_store_tree, u))

    # everydict + inline_refs
    results.append(await _bench_dict("store everydict+inline", di_store_tree, di_store_tree, s))
    results.append(await _bench_dict("read everydict+inline", di_read_tree, di_store_tree, r))
    results.append(await _bench_dict("update everydict+inline", di_update_tree, di_store_tree, u))

    uninstall_counters()
    print_results("Scenario: Market Catalog", results)
    return results


if __name__ == "__main__":
    asyncio.run(run_all())
