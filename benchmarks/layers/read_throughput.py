"""Read throughput ceiling — max reads/sec at each layer.

Measures peak read throughput by batching all reads into a single
snapshot/transaction, fully amortizing span overhead.

Layers:
  L0  raw rdbpy get (C++ bindings)
  L1  tkv snapshot get (codec, tuple keys)
  L3  DictView __getitem__ (view + container)
  L4  Shape .get() via Snapshot (term execution + view)

All layers use a single snapshot for N reads — no per-op span cost.
"""

from __future__ import annotations

import asyncio
import shutil
import sys
import tempfile
import time


sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

import rdbpy
from virtuals.tkv.codecs import BinaryCodec
from virtuals.tkv.storages.rocksdb import RocksDBStorage
from virtuals.tkv.tkv.storage import StorageProtocol

import eb_pv as pv
from eb_pv import Atomic, Snapshot
from eb_pv.adapters.storage import rocksdb_storage_inmemory
from everybase import Context
from everybase.abc import Seq
from everybase.shape import Shape


# ── Shape ─────────────────────────────────────────────────────────────


class FlatShape(Shape):
    value = pv.IntRef.slot()


# ── Config ────────────────────────────────────────────────────────────

N_SIZES = [1_000, 10_000, 50_000]
VALUE = 42


# ── L0: raw rdbpy ────────────────────────────────────────────────────


def bench_l0(n: int) -> float:
    key = b"k:0"
    tmpdir = tempfile.mkdtemp(prefix="bench_l0_tp_")
    try:
        opts = rdbpy.Options(create_if_missing=True)
        db = rdbpy.TransactionDB(tmpdir, opts)
        txn = db.begin_transaction()
        txn.put(key, b"42")
        txn.commit()
        txn.close()

        start = time.perf_counter()
        txn = db.begin_transaction()
        for _ in range(n):
            txn.get(key)
        txn.rollback()
        txn.close()
        elapsed = time.perf_counter() - start
        db.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return elapsed


# ── L1: tkv snapshot ──────────────────────────────────────────────────


def bench_l1(n: int) -> float:
    key = ("/", "value")
    tmpdir = tempfile.mkdtemp(prefix="bench_l1_tp_")
    try:
        with RocksDBStorage(path=tmpdir, codec=BinaryCodec(), observer=None) as storage:
            with storage.transaction() as tx:
                tx.put(key, VALUE)

            start = time.perf_counter()
            snap = storage.begin_snapshot()
            for _ in range(n):
                snap.get(key)
            snap.close()
            elapsed = time.perf_counter() - start
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return elapsed


# ── L3: DictView ──────────────────────────────────────────────────────


def bench_l3(n: int) -> float:
    from eb_pv.views import DictView

    tmpdir = tempfile.mkdtemp(prefix="bench_l3_tp_")
    try:
        with rocksdb_storage_inmemory(tmpdir) as storage:
            with storage.transaction() as tx:
                root = DictView.open_root(tx)
                root["value"] = VALUE

            start = time.perf_counter()
            snap = storage.begin_snapshot()
            root = DictView.open_root(snap)
            for _ in range(n):
                _ = root["value"]
            snap.close()
            elapsed = time.perf_counter() - start
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return elapsed


# ── L4: Shape via Snapshot ────────────────────────────────────────────


async def bench_l4(n: int) -> float:
    seed = Atomic(FlatShape.value.set(VALUE))
    batch = Snapshot(Seq(*[FlatShape.value.get() for _ in range(n)]), scope=FlatShape)

    tmpdir = tempfile.mkdtemp(prefix="bench_l4_tp_")
    try:
        with rocksdb_storage_inmemory(tmpdir) as storage:
            ctx = Context().bind(storage, StorageProtocol)
            await seed.execute(ctx)

            start = time.perf_counter()
            await batch.execute(ctx)
            elapsed = time.perf_counter() - start
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return elapsed


# ── Runner ────────────────────────────────────────────────────────────


async def main() -> None:
    print("Read Throughput Ceiling — single snapshot, N reads")
    print()

    for n in N_SIZES:
        t0 = bench_l0(n)
        t1 = bench_l1(n)
        t3 = bench_l3(n)
        t4 = await bench_l4(n)

        rows = [
            ("L0 rdbpy", t0),
            ("L1 tkv", t1),
            ("L3 DictView", t3),
            ("L4 Shape (Snapshot)", t4),
        ]

        print(f"  N = {n:,}")
        print(
            f"  {'Layer':<25s} {'Total (s)':>10s} {'Per-op (us)':>12s} {'reads/sec':>12s} {'vs L0':>8s}"
        )
        print(f"  {'-' * 25} {'-' * 10} {'-' * 12} {'-' * 12} {'-' * 8}")
        l0_per_op = t0 / n
        for label, t in rows:
            per_op = t / n
            per_op_us = per_op * 1_000_000
            rps = n / t if t > 0 else float("inf")
            ratio = per_op / l0_per_op if l0_per_op > 0 else 0
            print(f"  {label:<25s} {t:>10.4f} {per_op_us:>12.1f} {rps:>12,.0f} {ratio:>7.1f}x")
        print()


if __name__ == "__main__":
    asyncio.run(main())
