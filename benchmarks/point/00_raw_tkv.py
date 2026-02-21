"""Scenario 0: Raw TKV RocksDB — absolute storage floor.

Measures: pure RocksDB get/put/commit throughput via tkv layer.
No PV containers, no shapes, no term trees — just key-value I/O.
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


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


# tkv BinaryCodec expects tuple keys like ('/', 'segment', ...)
def _key(name: str, i: int | None = None) -> tuple[str, ...]:
    if i is not None:
        return ("/", name, str(i))
    return ("/", name)


# --------------------------------------------------------------------------
# Benchmarks
# --------------------------------------------------------------------------


async def bench_raw_put(n: int) -> TimingResult:
    """Raw txn.put() — 5 keys per op, one commit per op."""
    from tkv.codecs import BinaryCodec
    from tkv.storages.rocksdb import RocksDBStorage

    tmpdir = tempfile.mkdtemp(prefix="bench_raw_tkv_")
    try:
        with RocksDBStorage(path=tmpdir, codec=BinaryCodec(), observer=None) as storage:
            get_counters().reset()
            with timed_run(f"raw_put_5keys x{n}", n) as results:
                for i in range(n):
                    with storage.transaction() as tx:
                        tx.put(_key("f0", i), i)
                        tx.put(_key("f1", i), i * 2)
                        tx.put(_key("f2", i), f"v{i}")
                        tx.put(_key("f3", i), float(i) * 0.1)
                        tx.put(_key("f4", i), i + 100)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


async def bench_raw_put_1key(n: int) -> TimingResult:
    """Raw txn.put() — 1 key per txn."""
    from tkv.codecs import BinaryCodec
    from tkv.storages.rocksdb import RocksDBStorage

    tmpdir = tempfile.mkdtemp(prefix="bench_raw_tkv_")
    try:
        with RocksDBStorage(path=tmpdir, codec=BinaryCodec(), observer=None) as storage:
            get_counters().reset()
            with timed_run(f"raw_put_1key x{n}", n) as results:
                for i in range(n):
                    with storage.transaction() as tx:
                        tx.put(_key("k", i), i)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


async def bench_raw_get(n: int) -> TimingResult:
    """Raw snapshot.get() — read 5 keys per op."""
    from tkv.codecs import BinaryCodec
    from tkv.storages.rocksdb import RocksDBStorage

    tmpdir = tempfile.mkdtemp(prefix="bench_raw_tkv_")
    try:
        with RocksDBStorage(path=tmpdir, codec=BinaryCodec(), observer=None) as storage:
            # Seed data
            with storage.transaction() as tx:
                for i in range(n):
                    tx.put(_key("f0", i), i)
                    tx.put(_key("f1", i), i * 2)
                    tx.put(_key("f2", i), f"v{i}")
                    tx.put(_key("f3", i), float(i) * 0.1)
                    tx.put(_key("f4", i), i + 100)

            get_counters().reset()
            with timed_run(f"raw_get_5keys x{n}", n) as results:
                for i in range(n):
                    snap = storage.begin_snapshot()
                    snap.get(_key("f0", i))
                    snap.get(_key("f1", i))
                    snap.get(_key("f2", i))
                    snap.get(_key("f3", i))
                    snap.get(_key("f4", i))
                    snap.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


async def bench_raw_put_single_txn(n: int) -> TimingResult:
    """Raw txn.put() — 5 keys x N ops in a SINGLE transaction (1 commit total)."""
    from tkv.codecs import BinaryCodec
    from tkv.storages.rocksdb import RocksDBStorage

    tmpdir = tempfile.mkdtemp(prefix="bench_raw_tkv_")
    try:
        with RocksDBStorage(path=tmpdir, codec=BinaryCodec(), observer=None) as storage:
            get_counters().reset()
            with timed_run(f"raw_put_5keys_1txn x{n}", n) as results:
                with storage.transaction() as tx:
                    for i in range(n):
                        tx.put(_key("f0", i), i)
                        tx.put(_key("f1", i), i * 2)
                        tx.put(_key("f2", i), f"v{i}")
                        tx.put(_key("f3", i), float(i) * 0.1)
                        tx.put(_key("f4", i), i + 100)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


async def bench_raw_overwrite(n: int) -> TimingResult:
    """Raw txn.put() overwriting same 5 keys — simulates shape field updates."""
    from tkv.codecs import BinaryCodec
    from tkv.storages.rocksdb import RocksDBStorage

    tmpdir = tempfile.mkdtemp(prefix="bench_raw_tkv_")
    try:
        with RocksDBStorage(path=tmpdir, codec=BinaryCodec(), observer=None) as storage:
            # Seed initial values
            with storage.transaction() as tx:
                tx.put(_key("f0"), 0)
                tx.put(_key("f1"), 0)
                tx.put(_key("f2"), "init")
                tx.put(_key("f3"), 0.0)
                tx.put(_key("f4"), 0)

            get_counters().reset()
            with timed_run(f"raw_overwrite_5keys x{n}", n) as results:
                for i in range(n):
                    with storage.transaction() as tx:
                        tx.put(_key("f0"), i)
                        tx.put(_key("f1"), i * 2)
                        tx.put(_key("f2"), f"v{i}")
                        tx.put(_key("f3"), float(i) * 0.1)
                        tx.put(_key("f4"), i + 100)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------

N = 1000


async def run_all() -> list[TimingResult]:
    install_counters()
    results = []

    results.append(await bench_raw_put_1key(N))
    results.append(await bench_raw_put(N))
    results.append(await bench_raw_overwrite(N))
    results.append(await bench_raw_get(N))
    results.append(await bench_raw_put_single_txn(N))

    uninstall_counters()
    print_results("Scenario 0: Raw TKV RocksDB", results)
    return results


if __name__ == "__main__":
    asyncio.run(run_all())
