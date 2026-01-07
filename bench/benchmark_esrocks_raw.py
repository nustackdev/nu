"""Benchmark raw esrocks CPython bindings.

Tests common KV store operations directly on esrocks:
- put (set)
- get
- exists (get != None)
- iterator scan

Usage:
    python examples/benchmark_esrocks_raw.py [--num-keys N] [--value-size S]
"""

from __future__ import annotations

import argparse
import shutil
import time
from collections.abc import Callable
from pathlib import Path

import esrocks


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

    # Create options
    options = esrocks.Options(create_if_missing=True)

    # Open database (path, options)
    db = esrocks.TransactionDB(str(db_path), options)

    # Prepare test data
    keys = [f"key:{i:08d}".encode() for i in range(num_keys)]
    value = b"x" * value_size

    print("\nBenchmark: raw esrocks bindings")
    print(f"Keys: {num_keys:,}, Value size: {value_size} bytes")
    print("-" * 60)

    # =========================================================================
    # PUT benchmark (sequential writes in transaction)
    # =========================================================================
    def bench_put() -> int:
        txn = db.begin_transaction()
        for key in keys:
            txn.put(key, value)
        txn.commit()
        return len(keys)

    elapsed, ops = benchmark("put", bench_put)
    print(f"put (txn):      {elapsed:.3f}s | {format_ops_per_sec(ops, elapsed):>12} ops/s")

    # =========================================================================
    # GET benchmark (sequential reads in transaction)
    # =========================================================================
    def bench_get() -> int:
        txn = db.begin_transaction()
        for key in keys:
            _ = txn.get(key)
        txn.rollback()
        return len(keys)

    elapsed, ops = benchmark("get", bench_get)
    print(f"get (txn):      {elapsed:.3f}s | {format_ops_per_sec(ops, elapsed):>12} ops/s")

    # =========================================================================
    # EXISTS benchmark (check if key exists)
    # =========================================================================
    def bench_exists() -> int:
        txn = db.begin_transaction()
        for key in keys:
            _ = txn.get(key) is not None
        txn.rollback()
        return len(keys)

    elapsed, ops = benchmark("exists", bench_exists)
    print(f"exists (txn):   {elapsed:.3f}s | {format_ops_per_sec(ops, elapsed):>12} ops/s")

    # =========================================================================
    # ITERATOR KEYS benchmark (scan all keys)
    # =========================================================================
    def bench_iter_keys() -> int:
        txn = db.begin_transaction()
        it = txn.iterkeys()
        it.seek_to_first()
        count = 0
        while True:
            try:
                _ = it.get()
                count += 1
                it.skip()
            except (ValueError, IndexError):
                break
        txn.rollback()
        return count

    elapsed, ops = benchmark("iter_keys", bench_iter_keys)
    print(f"iter keys:      {elapsed:.3f}s | {format_ops_per_sec(ops, elapsed):>12} ops/s")

    # =========================================================================
    # ITERATOR ITEMS benchmark (scan all key-value pairs)
    # =========================================================================
    def bench_iter_items() -> int:
        txn = db.begin_transaction()
        it = txn.iteritems()
        it.seek_to_first()
        count = 0
        while True:
            try:
                _ = it.get()
                count += 1
                it.skip()
            except (ValueError, IndexError):
                break
        txn.rollback()
        return count

    elapsed, ops = benchmark("iter_items", bench_iter_items)
    print(f"iter items:     {elapsed:.3f}s | {format_ops_per_sec(ops, elapsed):>12} ops/s")

    # =========================================================================
    # BATCH WRITE benchmark (using WriteBatch)
    # =========================================================================
    # First delete all keys so we can test batch insert
    txn = db.begin_transaction()
    for key in keys:
        try:
            txn.delete_single(key)
        except Exception:
            pass
    txn.commit()

    def bench_batch_put() -> int:
        batch = esrocks.WriteBatch()
        for key in keys:
            batch.put(key, value)
        db.write(batch)
        return len(keys)

    elapsed, ops = benchmark("batch_put", bench_batch_put)
    print(f"batch put:      {elapsed:.3f}s | {format_ops_per_sec(ops, elapsed):>12} ops/s")

    # =========================================================================
    # Direct DB GET benchmark (no transaction overhead)
    # =========================================================================
    def bench_direct_get() -> int:
        for key in keys:
            _ = db.get(key)
        return len(keys)

    elapsed, ops = benchmark("direct_get", bench_direct_get)
    print(f"get (direct):   {elapsed:.3f}s | {format_ops_per_sec(ops, elapsed):>12} ops/s")

    print("-" * 60)

    # Cleanup
    db.close()
    shutil.rmtree(db_path)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Benchmark raw esrocks bindings")
    parser.add_argument("--num-keys", type=int, default=100_000, help="Number of keys to test")
    parser.add_argument("--value-size", type=int, default=100, help="Size of values in bytes")
    parser.add_argument(
        "--db-path",
        type=Path,
        default=Path(".bench_esrocks_raw"),
        help="Database path",
    )
    args = parser.parse_args()

    run_benchmarks(args.num_keys, args.value_size, args.db_path)


if __name__ == "__main__":
    main()
