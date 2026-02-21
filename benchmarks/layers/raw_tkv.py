"""Raw TKV RocksDB -- absolute storage floor.

Measures pure RocksDB get/put/commit throughput via the tkv layer.
No PV containers, no shapes, no term trees -- just key-value I/O.

All keys are pre-built. Benchmark loops measure only execution.
"""

from __future__ import annotations

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


# -- Pre-built keys -----------------------------------------------------------

N = 1000

# Single-key operations
KEYS_1 = [("/", "k", str(i)) for i in range(N)]

# 5-field operations (simulates shape with 5 fields)
KEYS_5 = [[("/", f"f{f}", str(i)) for f in range(5)] for i in range(N)]

# Fixed 5-field keys for overwrite benchmark
KEYS_FIXED = [("/", f"f{f}") for f in range(5)]


# -- Helpers -------------------------------------------------------------------

VALUES_INT = list(range(N))
VALUES_STR = [f"v{i}" for i in range(N)]
VALUES_FLOAT = [float(i) * 0.1 for i in range(N)]


# -- Benchmarks ----------------------------------------------------------------


def bench_raw_put(n: int) -> TimingResult:
    """Raw txn.put() -- 5 keys per op, one commit per op."""
    from tkv.codecs import BinaryCodec
    from tkv.storages.rocksdb import RocksDBStorage

    tmpdir = tempfile.mkdtemp(prefix="bench_raw_tkv_")
    try:
        with RocksDBStorage(path=tmpdir, codec=BinaryCodec(), observer=None) as storage:
            get_counters().reset()
            with timed_run(f"raw_put_5keys x{n}", n) as results:
                for i in range(n):
                    with storage.transaction() as tx:
                        keys = KEYS_5[i]
                        tx.put(keys[0], VALUES_INT[i])
                        tx.put(keys[1], VALUES_INT[i] * 2)
                        tx.put(keys[2], VALUES_STR[i])
                        tx.put(keys[3], VALUES_FLOAT[i])
                        tx.put(keys[4], VALUES_INT[i] + 100)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


def bench_raw_put_1key(n: int) -> TimingResult:
    """Raw txn.put() -- 1 key per txn."""
    from tkv.codecs import BinaryCodec
    from tkv.storages.rocksdb import RocksDBStorage

    tmpdir = tempfile.mkdtemp(prefix="bench_raw_tkv_")
    try:
        with RocksDBStorage(path=tmpdir, codec=BinaryCodec(), observer=None) as storage:
            get_counters().reset()
            with timed_run(f"raw_put_1key x{n}", n) as results:
                for i in range(n):
                    with storage.transaction() as tx:
                        tx.put(KEYS_1[i], VALUES_INT[i])
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


def bench_raw_get(n: int) -> TimingResult:
    """Raw snapshot.get() -- read 5 keys per op."""
    from tkv.codecs import BinaryCodec
    from tkv.storages.rocksdb import RocksDBStorage

    tmpdir = tempfile.mkdtemp(prefix="bench_raw_tkv_")
    try:
        with RocksDBStorage(path=tmpdir, codec=BinaryCodec(), observer=None) as storage:
            # Seed data
            with storage.transaction() as tx:
                for i in range(n):
                    keys = KEYS_5[i]
                    tx.put(keys[0], VALUES_INT[i])
                    tx.put(keys[1], VALUES_INT[i] * 2)
                    tx.put(keys[2], VALUES_STR[i])
                    tx.put(keys[3], VALUES_FLOAT[i])
                    tx.put(keys[4], VALUES_INT[i] + 100)

            get_counters().reset()
            with timed_run(f"raw_get_5keys x{n}", n) as results:
                for i in range(n):
                    keys = KEYS_5[i]
                    snap = storage.begin_snapshot()
                    snap.get(keys[0])
                    snap.get(keys[1])
                    snap.get(keys[2])
                    snap.get(keys[3])
                    snap.get(keys[4])
                    snap.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


def bench_raw_put_single_txn(n: int) -> TimingResult:
    """Raw txn.put() -- 5 keys x N ops in a SINGLE transaction (1 commit total)."""
    from tkv.codecs import BinaryCodec
    from tkv.storages.rocksdb import RocksDBStorage

    tmpdir = tempfile.mkdtemp(prefix="bench_raw_tkv_")
    try:
        with RocksDBStorage(path=tmpdir, codec=BinaryCodec(), observer=None) as storage:
            get_counters().reset()
            with timed_run(f"raw_put_5keys_1txn x{n}", n) as results:
                with storage.transaction() as tx:
                    for i in range(n):
                        keys = KEYS_5[i]
                        tx.put(keys[0], VALUES_INT[i])
                        tx.put(keys[1], VALUES_INT[i] * 2)
                        tx.put(keys[2], VALUES_STR[i])
                        tx.put(keys[3], VALUES_FLOAT[i])
                        tx.put(keys[4], VALUES_INT[i] + 100)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


def bench_raw_overwrite(n: int) -> TimingResult:
    """Raw txn.put() overwriting same 5 keys -- simulates shape field updates."""
    from tkv.codecs import BinaryCodec
    from tkv.storages.rocksdb import RocksDBStorage

    tmpdir = tempfile.mkdtemp(prefix="bench_raw_tkv_")
    try:
        with RocksDBStorage(path=tmpdir, codec=BinaryCodec(), observer=None) as storage:
            # Seed initial values
            with storage.transaction() as tx:
                tx.put(KEYS_FIXED[0], 0)
                tx.put(KEYS_FIXED[1], 0)
                tx.put(KEYS_FIXED[2], "init")
                tx.put(KEYS_FIXED[3], 0.0)
                tx.put(KEYS_FIXED[4], 0)

            get_counters().reset()
            with timed_run(f"raw_overwrite_5keys x{n}", n) as results:
                for i in range(n):
                    with storage.transaction() as tx:
                        tx.put(KEYS_FIXED[0], VALUES_INT[i])
                        tx.put(KEYS_FIXED[1], VALUES_INT[i] * 2)
                        tx.put(KEYS_FIXED[2], VALUES_STR[i])
                        tx.put(KEYS_FIXED[3], VALUES_FLOAT[i])
                        tx.put(KEYS_FIXED[4], VALUES_INT[i] + 100)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


# -- Runner --------------------------------------------------------------------


def run_all() -> list[TimingResult]:
    install_counters()
    results = []

    results.append(bench_raw_put_1key(N))
    results.append(bench_raw_put(N))
    results.append(bench_raw_overwrite(N))
    results.append(bench_raw_get(N))
    results.append(bench_raw_put_single_txn(N))

    uninstall_counters()
    print_results("Raw TKV RocksDB", results)
    return results


if __name__ == "__main__":
    run_all()
