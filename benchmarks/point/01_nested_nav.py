"""Nested Shape Navigation -- read/write at different depths and view types.

Measures:
- Dict-only paths at depth 2/4/6 (static addresses → fast path)
- Mixed dict+list paths (static positive index → fast path)
- Negative list index paths (dynamic normalization → slow path)

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
from everypv import Atomic
from everyshape import Shape


# ── Shapes ────────────────────────────────────────────────────────────


class Leaf(Shape):
    value = pv.IntRef.slot()
    label = pv.StrRef.slot()


class L5(Shape):
    inner = pv.ShapeRef.slot(shape_type=Leaf)
    count = pv.IntRef.slot()


class L4(Shape):
    inner = pv.ShapeRef.slot(shape_type=L5)
    count = pv.IntRef.slot()


class L3(Shape):
    inner = pv.ShapeRef.slot(shape_type=L4)
    count = pv.IntRef.slot()


class L2(Shape):
    inner = pv.ShapeRef.slot(shape_type=L3)
    count = pv.IntRef.slot()


class Root(Shape):
    inner = pv.ShapeRef.slot(shape_type=L2)
    count = pv.IntRef.slot()


# ── Shapes with lists ────────────────────────────────────────────────


class ItemShape(Shape):
    value = pv.IntRef.slot()


class WithList(Shape):
    items = pv.ListRef.slot(item_type=int)
    nested = pv.ShapeRef.slot(shape_type=ItemShape)


class ListRoot(Shape):
    data = pv.ShapeRef.slot(shape_type=WithList)


# ── Pre-built terms ──────────────────────────────────────────────────

# Dict-only paths (all static addresses)
DICT_TERMS = {
    "d2_write": Atomic(Root.inner.count.set(42)),
    "d4_write": Atomic(Root.inner.inner.inner.count.set(42)),
    "d6_write": Atomic(Root.inner.inner.inner.inner.inner.value.set(42)),
    "d2_read": Atomic(Root.inner.count.get()),
    "d4_read": Atomic(Root.inner.inner.inner.count.get()),
    "d6_read": Atomic(Root.inner.inner.inner.inner.inner.value.get()),
}

DICT_SEEDS = {
    "d2": Atomic(Root.inner.count.set(42)),
    "d4": Atomic(Root.inner.inner.inner.count.set(42)),
    "d6": Atomic(Root.inner.inner.inner.inner.inner.value.set(42)),
}

# List paths — positive index (static address → fast path)
LIST_SEED = Atomic(
    Seq(
        ListRoot.data.nested.value.set(99),
        ListRoot.data.items.set([10, 20, 30, 40, 50]),
    )
)

LIST_TERMS = {
    "list_pos_read": Atomic(ListRoot.data.items[0].get()),
    "list_pos_write": Atomic(ListRoot.data.items[2].set(999)),
    # Negative index — triggers normalize_address (slow path)
    "list_neg_read": Atomic(ListRoot.data.items[-1].get()),
    "list_neg_write": Atomic(ListRoot.data.items[-1].set(999)),
    # Mixed: dict nav + list access
    "mixed_pos_read": Atomic(ListRoot.data.items[4].get()),
    "mixed_neg_read": Atomic(ListRoot.data.items[-2].get()),
}


# ── Benchmarks ───────────────────────────────────────────────────────

N = 100


async def _bench(label: str, term, seed_term, seed_key: str | None = None) -> TimingResult:
    """Benchmark with fresh db per measurement."""
    tmpdir = tempfile.mkdtemp(prefix="bench_nested_")
    try:
        from everypv.adapters.storage import rocksdb_storage_inmemory

        with rocksdb_storage_inmemory(tmpdir) as storage:
            ctx = Context().with_handle(StorageProtocol, storage)
            await seed_term.execute(ctx)
            get_counters().reset()

            with timed_run(label, N) as results:
                for _ in range(N):
                    await term.execute(ctx)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


# ── Runner ───────────────────────────────────────────────────────────


async def run_all() -> list[TimingResult]:
    install_counters()
    results = []

    # --- Dict-only paths (static) ---
    for key in ("d2_write", "d4_write", "d6_write"):
        depth = key.split("_")[0]
        results.append(await _bench(f"{key} x{N}", DICT_TERMS[key], DICT_SEEDS[depth]))

    for key in ("d2_read", "d4_read", "d6_read"):
        depth = key.split("_")[0]
        results.append(await _bench(f"{key} x{N}", DICT_TERMS[key], DICT_SEEDS[depth]))

    # --- List paths ---
    for key in (
        "list_pos_read",
        "list_pos_write",
        "list_neg_read",
        "list_neg_write",
        "mixed_pos_read",
        "mixed_neg_read",
    ):
        results.append(await _bench(f"{key} x{N}", LIST_TERMS[key], LIST_SEED))

    uninstall_counters()
    print_results("Nested Shape Navigation", results)
    return results


if __name__ == "__main__":
    asyncio.run(run_all())
