"""Benchmark RocksDBStorage wrapper.

Tests common KV store operations through the RocksDBStorage abstraction:
- put (set)
- get
- has (exists)
- scan iterator (keys, items)

Usage:
    python examples/benchmark_rocks_storage.py [--num-keys N] [--value-size S]
"""

from __future__ import annotations

import argparse
import shutil
import time
from collections.abc import Callable
from pathlib import Path

from everyshape.adapters import BinaryCodec, RocksDBStorage
from everyshape.storage import StorageScanOptions


def format_ops_per_sec(ops: int, elapsed: float) -> str:
    """Format operations per second."""
    if elapsed == 0:
        return "inf"
    return f"{ops / elapsed:,.0f}"


def benchmark(_name: str, func: Callable[[], int], iterations: int = 1) -> tuple[float, int]:
    """Run a benchmark and return elapsed time and operation count."""
    total_ops = 0
    start = time.perf_counter()
    for _ in range(iterations):
        total_ops += func()
    elapsed = time.perf_counter() - start
    return elapsed, total_ops


def run_benchmarks(num_keys: int, value_size: int, db_path: Path) -> None:
    """Run all benchmarks."""
    # Clean up any existing db
    if db_path.exists():
        shutil.rmtree(db_path)
    db_path.mkdir(parents=True, exist_ok=True)

    # Create storage with BinaryCodec
    codec = BinaryCodec()
    storage = RocksDBStorage(path=db_path, codec=codec)
    storage.open()

    # Prepare test data - using tuple keys for the Key type
    keys: list[tuple[str, ...]] = [("bench", f"{i:08d}") for i in range(num_keys)]
    value = "x" * value_size  # String value for the codec

    print("\nBenchmark: RocksDBStorage wrapper")
    print(f"Keys: {num_keys:,}, Value size: {value_size} bytes")
    print("-" * 60)

    # =========================================================================
    # PUT benchmark (sequential writes in transaction)
    # =========================================================================
    def bench_put() -> int:
        with storage.transaction() as txn:
            for key in keys:
                txn.put(key, value)
        return len(keys)

    elapsed, ops = benchmark("put", bench_put)
    print(f"put (txn):      {elapsed:.3f}s | {format_ops_per_sec(ops, elapsed):>12} ops/s")

    # =========================================================================
    # GET benchmark (sequential reads in snapshot)
    # =========================================================================
    def bench_get() -> int:
        with storage.snapshot() as snap:
            for key in keys:
                try:
                    _ = snap.get(key)
                except Exception:
                    pass
        return len(keys)

    elapsed, ops = benchmark("get", bench_get)
    print(f"get (snap):     {elapsed:.3f}s | {format_ops_per_sec(ops, elapsed):>12} ops/s")

    # =========================================================================
    # HAS (exists) benchmark
    # =========================================================================
    def bench_has() -> int:
        with storage.snapshot() as snap:
            for key in keys:
                _ = snap.has(key)
        return len(keys)

    elapsed, ops = benchmark("has", bench_has)
    print(f"has (snap):     {elapsed:.3f}s | {format_ops_per_sec(ops, elapsed):>12} ops/s")

    # =========================================================================
    # SCAN KEYS benchmark (iterate all keys)
    # =========================================================================
    def bench_scan_keys() -> int:
        with storage.snapshot() as snap:
            scan_opts = StorageScanOptions(
                start=("bench",),
                end=("bench", "\xff"),
                start_inclusive=True,
                end_inclusive=False,
            )
            scan = snap.scan(scan_opts)
            count = 0
            for _ in scan.keys():
                count += 1
        return count

    elapsed, ops = benchmark("scan_keys", bench_scan_keys)
    print(f"scan keys:      {elapsed:.3f}s | {format_ops_per_sec(ops, elapsed):>12} ops/s")

    # =========================================================================
    # SCAN ITEMS benchmark (iterate all key-value pairs)
    # =========================================================================
    def bench_scan_items() -> int:
        with storage.snapshot() as snap:
            scan_opts = StorageScanOptions(
                start=("bench",),
                end=("bench", "\xff"),
                start_inclusive=True,
                end_inclusive=False,
            )
            scan = snap.scan(scan_opts)
            count = 0
            for _ in scan.items():
                count += 1
        return count

    elapsed, ops = benchmark("scan_items", bench_scan_items)
    print(f"scan items:     {elapsed:.3f}s | {format_ops_per_sec(ops, elapsed):>12} ops/s")

    # =========================================================================
    # MULTIGET benchmark
    # =========================================================================
    def bench_multiget() -> int:
        with storage.snapshot() as snap:
            # Get subset of keys in batches
            batch_size = min(100, num_keys)
            batch_keys = keys[:batch_size]
            result = snap.multiget(list(batch_keys))
            return len(result)

    elapsed, ops = benchmark("multiget", bench_multiget)
    print(f"multiget:       {elapsed:.3f}s | {format_ops_per_sec(ops, elapsed):>12} ops/s")

    # =========================================================================
    # WRITE BATCH benchmark
    # =========================================================================
    # First delete all keys
    with storage.transaction() as txn:
        for key in keys:
            txn.delete(key)

    def bench_write_batch() -> int:
        with storage.batch_write() as batch:
            for key in keys:
                batch.put(key, value)
        return len(keys)

    elapsed, ops = benchmark("write_batch", bench_write_batch)
    print(f"batch put:      {elapsed:.3f}s | {format_ops_per_sec(ops, elapsed):>12} ops/s")

    # =========================================================================
    # Transaction GET benchmark (read in transaction context)
    # =========================================================================
    def bench_txn_get() -> int:
        with storage.transaction() as txn:
            for key in keys:
                try:
                    _ = txn.get(key)
                except Exception:
                    pass
        return len(keys)

    elapsed, ops = benchmark("txn_get", bench_txn_get)
    print(f"get (txn):      {elapsed:.3f}s | {format_ops_per_sec(ops, elapsed):>12} ops/s")

    print("-" * 60)

    # Cleanup
    storage.close()
    shutil.rmtree(db_path)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Benchmark RocksDBStorage wrapper")
    parser.add_argument("--num-keys", type=int, default=100_000, help="Number of keys to test")
    parser.add_argument("--value-size", type=int, default=100, help="Size of values in bytes")
    parser.add_argument(
        "--db-path",
        type=Path,
        default=Path(".bench_rocks_storage"),
        help="Database path",
    )
    args = parser.parse_args()

    run_benchmarks(args.num_keys, args.value_size, args.db_path)


if __name__ == "__main__":
    main()
