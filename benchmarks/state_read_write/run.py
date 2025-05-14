"""
Enhanced KV Storage Benchmark Tool

This benchmarks a key-value storage system with four phases:
1. Populate: Fill storage with random numbers
2. Read: Perform random reads to test retrieval performance
3. Alter: Perform random updates to test write performance
4. Dump: Clear all storage and measure cleanup performance

The tool uses detailed timing metrics to measure performance across all operations.
"""

from __future__ import annotations

import asyncio
import random
import statistics
import time
from pathlib import Path

from loomi import AsyncApp, Context, Operation
from loomistd.aexecutor import ExecutionEngineSpec
from loomistd.kv.in_memory import InMemoryStorageSpec
from loomistd.kv.lmdb import LMDBStorageSpec
from loomistd.state import StateSpec
from loomix.logging import setup_logging

# Basic setup
setup_logging(Path(".logs"), log_level=10)

# Constants
NUM_ENTRIES = 100_000
NUM_READS = 100_000
NUM_UPDATES = 100_000
BATCH_SIZE = 1000  # Process in batches for better performance
READ_PATTERNS = ["sequential", "random", "repeated"]  # Different read patterns to benchmark

# Configure service specs - can switch between in-memory and LMDB
USE_LMDB = True  # Set to True to use LMDB instead of in-memory storage

if USE_LMDB:
    state_spec = StateSpec(storage=LMDBStorageSpec())
else:
    state_spec = StateSpec(storage=InMemoryStorageSpec())

executor_spec = ExecutionEngineSpec(state=state_spec)


class BenchmarkApp(AsyncApp):
    async def setup(self, context: Context):
        self.metrics = {
            "populate": {"start": 0, "end": 0, "batches": []},
            "read": {"start": 0, "end": 0, "batches": [], "patterns": {}},
            "alter": {"start": 0, "end": 0, "batches": []},
            "dump": {"start": 0, "end": 0, "batches": []},
        }

        # Initialize metrics for each read pattern
        for pattern in READ_PATTERNS:
            self.metrics["read"]["patterns"][pattern] = {
                "start": 0,
                "end": 0,
                "batches": [],
                "hit_rate": 0,
                "miss_rate": 0,
            }

    async def populate_storage(self, context: Context):
        """Populate storage with 1 million random numbers."""
        self.metrics["populate"]["start"] = time.time()
        print(f"\n[{time.strftime('%H:%M:%S')}] Starting population phase...")

        # Process in batches
        for batch_idx in range(0, NUM_ENTRIES, BATCH_SIZE):
            batch_start = time.time()
            with self.state.transaction() as txn:
                obj = context.scope.dict("data", txn=txn)

                # Generate and store batch of random numbers
                for i in range(batch_idx, min(batch_idx + BATCH_SIZE, NUM_ENTRIES)):
                    key = f"key_{i}"
                    value = random.randint(1, 10000)
                    obj.set(key, value=value)

            batch_time = time.time() - batch_start
            self.metrics["populate"]["batches"].append(batch_time)

            # Progress update every 10 batches
            if (batch_idx // BATCH_SIZE) % 10 == 0:
                progress = min(100, (batch_idx + BATCH_SIZE) * 100 // NUM_ENTRIES)
                print(f"  Population {progress}% complete, batch time: {batch_time:.4f}s")

        self.metrics["populate"]["end"] = time.time()
        total_time = self.metrics["populate"]["end"] - self.metrics["populate"]["start"]
        print(f"[{time.strftime('%H:%M:%S')}] Population complete in {total_time:.2f}s")

        # Count items to verify
        count = await self._count_items(context)
        print(f"  Verified {count} items in storage")

    async def read_storage(self, context: Context):  # noqa: C901
        """Benchmark different read patterns."""
        self.metrics["read"]["start"] = time.time()
        print(f"\n[{time.strftime('%H:%M:%S')}] Starting read phase...")

        # Test different read patterns
        for pattern in READ_PATTERNS:
            print(f"  Testing '{pattern}' read pattern...")
            self.metrics["read"]["patterns"][pattern]["start"] = time.time()
            hits, misses = 0, 0

            if pattern == "sequential":
                # Sequential reads from start to end
                for batch_idx in range(0, NUM_READS, BATCH_SIZE):
                    batch_start = time.time()
                    with self.state.transaction() as txn:
                        obj = context.scope.dict("data", txn=txn)

                        for i in range(batch_idx, min(batch_idx + BATCH_SIZE, NUM_READS)):
                            key = f"key_{i % NUM_ENTRIES}"
                            try:
                                value = obj.get(key)
                                if value is not None:
                                    hits += 1
                                else:
                                    misses += 1
                            except Exception:
                                misses += 1

                    batch_time = time.time() - batch_start
                    self.metrics["read"]["patterns"][pattern]["batches"].append(batch_time)

                    # Progress update
                    if (batch_idx // BATCH_SIZE) % 10 == 0:
                        progress = min(100, (batch_idx + BATCH_SIZE) * 100 // NUM_READS)
                        print(f"    {progress}% complete, batch time: {batch_time:.4f}s")

            elif pattern == "random":
                # Random reads
                for batch_idx in range(0, NUM_READS, BATCH_SIZE):
                    batch_start = time.time()
                    with self.state.transaction() as txn:
                        obj = context.scope.dict("data", txn=txn)

                        for i in range(batch_idx, min(batch_idx + BATCH_SIZE, NUM_READS)):
                            key = f"key_{random.randint(0, NUM_ENTRIES * 2)}"  # Intentionally include some out-of-range keys
                            try:
                                value = obj.get(key)
                                if value is not None:
                                    hits += 1
                                else:
                                    misses += 1
                            except Exception:
                                misses += 1

                    batch_time = time.time() - batch_start
                    self.metrics["read"]["patterns"][pattern]["batches"].append(batch_time)

                    # Progress update
                    if (batch_idx // BATCH_SIZE) % 10 == 0:
                        progress = min(100, (batch_idx + BATCH_SIZE) * 100 // NUM_READS)
                        print(f"    {progress}% complete, batch time: {batch_time:.4f}s")

            elif pattern == "repeated":
                # Repeated reads of hot keys (simulates cache behavior)
                hot_keys = [f"key_{random.randint(0, NUM_ENTRIES - 1)}" for _ in range(10)]

                for batch_idx in range(0, NUM_READS, BATCH_SIZE):
                    batch_start = time.time()
                    with self.state.transaction() as txn:
                        obj = context.scope.dict("data", txn=txn)

                        for i in range(batch_idx, min(batch_idx + BATCH_SIZE, NUM_READS)):
                            # 80% hot keys, 20% random keys
                            if random.random() < 0.8:
                                key = random.choice(hot_keys)
                            else:
                                key = f"key_{random.randint(0, NUM_ENTRIES - 1)}"

                            try:
                                value = obj.get(key)
                                if value is not None:
                                    hits += 1
                                else:
                                    misses += 1
                            except Exception:
                                misses += 1

                    batch_time = time.time() - batch_start
                    self.metrics["read"]["patterns"][pattern]["batches"].append(batch_time)

                    # Progress update
                    if (batch_idx // BATCH_SIZE) % 10 == 0:
                        progress = min(100, (batch_idx + BATCH_SIZE) * 100 // NUM_READS)
                        print(f"    {progress}% complete, batch time: {batch_time:.4f}s")

            # Calculate hit rate
            total = hits + misses
            hit_rate = (hits / total) * 100 if total > 0 else 0
            miss_rate = (misses / total) * 100 if total > 0 else 0

            self.metrics["read"]["patterns"][pattern]["hit_rate"] = hit_rate
            self.metrics["read"]["patterns"][pattern]["miss_rate"] = miss_rate
            self.metrics["read"]["patterns"][pattern]["end"] = time.time()

            pattern_time = (
                self.metrics["read"]["patterns"][pattern]["end"]
                - self.metrics["read"]["patterns"][pattern]["start"]
            )
            print(
                f"    '{pattern}' complete in {pattern_time:.2f}s, hit rate: {hit_rate:.1f}%, miss rate: {miss_rate:.1f}%"
            )

        # Overall read phase timing
        self.metrics["read"]["end"] = time.time()
        total_time = self.metrics["read"]["end"] - self.metrics["read"]["start"]
        print(f"[{time.strftime('%H:%M:%S')}] Read phase complete in {total_time:.2f}s")

    async def alter_storage(self, context: Context):
        """Randomly update entries."""
        self.metrics["alter"]["start"] = time.time()
        print(f"\n[{time.strftime('%H:%M:%S')}] Starting alteration phase...")

        # Process updates in batches
        for batch_idx in range(0, NUM_UPDATES, BATCH_SIZE):
            batch_start = time.time()
            with self.state.transaction() as txn:
                obj = context.scope.dict("data", txn=txn)

                # Perform random updates
                for i in range(batch_idx, min(batch_idx + BATCH_SIZE, NUM_UPDATES)):
                    key = f"key_{random.randint(0, NUM_ENTRIES - 1)}"
                    value = random.randint(1, 10000)
                    obj.set(key, value=value)

            batch_time = time.time() - batch_start
            self.metrics["alter"]["batches"].append(batch_time)

            # Progress update every 10 batches
            if (batch_idx // BATCH_SIZE) % 10 == 0:
                progress = min(100, (batch_idx + BATCH_SIZE) * 100 // NUM_UPDATES)
                print(f"  Alteration {progress}% complete, batch time: {batch_time:.4f}s")

        self.metrics["alter"]["end"] = time.time()
        total_time = self.metrics["alter"]["end"] - self.metrics["alter"]["start"]
        print(f"[{time.strftime('%H:%M:%S')}] Alteration complete in {total_time:.2f}s")

    async def dump_storage(self, context: Context):
        """Clear all storage."""
        self.metrics["dump"]["start"] = time.time()
        print(f"\n[{time.strftime('%H:%M:%S')}] Starting dump phase...")

        # Count items before clearing
        count_before = await self._count_items(context)
        print(f"  Items before dump: {count_before}")

        # Process deletion in batches
        for batch_idx in range(0, NUM_ENTRIES, BATCH_SIZE):
            batch_start = time.time()
            with self.state.transaction() as txn:
                obj = context.scope.dict("data", txn=txn)

                # Delete batch of keys
                for i in range(batch_idx, min(batch_idx + BATCH_SIZE, NUM_ENTRIES)):
                    key = f"key_{i}"
                    obj.remove(key)

            batch_time = time.time() - batch_start
            self.metrics["dump"]["batches"].append(batch_time)

            # Progress update every 10 batches
            if (batch_idx // BATCH_SIZE) % 10 == 0:
                progress = min(100, (batch_idx + BATCH_SIZE) * 100 // NUM_ENTRIES)
                print(f"  Dump {progress}% complete, batch time: {batch_time:.4f}s")

        # Verify storage is empty
        count_after = await self._count_items(context)
        print(f"  Items after dump: {count_after}")

        self.metrics["dump"]["end"] = time.time()
        total_time = self.metrics["dump"]["end"] - self.metrics["dump"]["start"]
        print(f"[{time.strftime('%H:%M:%S')}] Dump complete in {total_time:.2f}s")

    async def _count_items(self, context: Context) -> int:
        """Helper to count items in storage."""
        keys = 0
        with self.state.transaction() as txn:
            obj = context.scope.dict("data", txn=txn)
            keys = len(list(obj.keys()))
        return keys

    async def print_report(self, context: Context):
        """Print performance report."""
        print("\n" + "=" * 50)
        print("BENCHMARK PERFORMANCE REPORT")
        print("=" * 50)

        storage_type = "LMDB" if USE_LMDB else "In-Memory"
        print(f"Storage Type: {storage_type}")
        print(f"Entries: {NUM_ENTRIES:,}")
        print(f"Reads: {NUM_READS:,}")
        print(f"Updates: {NUM_UPDATES:,}")
        print(f"Batch Size: {BATCH_SIZE:,}")

        total_time = sum(
            [
                self.metrics["populate"]["end"] - self.metrics["populate"]["start"],
                self.metrics["read"]["end"] - self.metrics["read"]["start"],
                self.metrics["alter"]["end"] - self.metrics["alter"]["start"],
                self.metrics["dump"]["end"] - self.metrics["dump"]["start"],
            ]
        )

        print("\nTiming Results:")
        print(f"  Total benchmark time: {total_time:.2f}s")

        # Standard phases (populate, alter, dump)
        for phase in ["populate", "alter", "dump"]:
            phase_time = self.metrics[phase]["end"] - self.metrics[phase]["start"]
            batch_times = self.metrics[phase]["batches"]

            if not batch_times:
                continue

            print(f"\n  {phase.capitalize()} phase:")
            print(f"    Total time: {phase_time:.2f}s")
            print(f"    Average batch time: {statistics.mean(batch_times):.4f}s")
            print(f"    Median batch time: {statistics.median(batch_times):.4f}s")
            print(f"    Min batch time: {min(batch_times):.4f}s")
            print(f"    Max batch time: {max(batch_times):.4f}s")

            total_ops = NUM_ENTRIES if phase != "alter" else NUM_UPDATES
            ops_per_sec = total_ops / phase_time if phase_time > 0 else 0
            print(f"    Operations per second: {ops_per_sec:.1f}")

        # Read phase (with patterns)
        print("\n  Read phase:")
        read_time = self.metrics["read"]["end"] - self.metrics["read"]["start"]
        print(f"    Total time: {read_time:.2f}s")

        # Print details for each read pattern
        for pattern in READ_PATTERNS:
            pattern_data = self.metrics["read"]["patterns"][pattern]
            pattern_time = pattern_data["end"] - pattern_data["start"]
            batch_times = pattern_data["batches"]

            if not batch_times:
                continue

            print(f"\n    {pattern.capitalize()} pattern:")
            print(f"      Time: {pattern_time:.2f}s")
            print(f"      Average batch time: {statistics.mean(batch_times):.4f}s")
            print(f"      Median batch time: {statistics.median(batch_times):.4f}s")
            print(f"      Min batch time: {min(batch_times):.4f}s")
            print(f"      Max batch time: {max(batch_times):.4f}s")
            print(f"      Hit rate: {pattern_data['hit_rate']:.1f}%")
            print(f"      Miss rate: {pattern_data['miss_rate']:.1f}%")

            ops_per_sec = NUM_READS / pattern_time if pattern_time > 0 else 0
            print(f"      Operations per second: {ops_per_sec:.1f}")

        # Summary table
        print("\n  Performance Summary:")
        print("  " + "-" * 48)
        print("  | {:^15} | {:^12} | {:^15} |".format("Operation", "Time (s)", "Ops/sec"))
        print("  " + "-" * 48)

        # Add each phase to the summary
        populate_time = self.metrics["populate"]["end"] - self.metrics["populate"]["start"]
        read_time = self.metrics["read"]["end"] - self.metrics["read"]["start"]
        alter_time = self.metrics["alter"]["end"] - self.metrics["alter"]["start"]
        dump_time = self.metrics["dump"]["end"] - self.metrics["dump"]["start"]

        print(
            "  | {:^15} | {:^12.2f} | {:^15.1f} |".format(
                "Populate", populate_time, NUM_ENTRIES / populate_time if populate_time > 0 else 0
            )
        )
        print(
            "  | {:^15} | {:^12.2f} | {:^15.1f} |".format(
                "Read", read_time, NUM_READS * 3 / read_time if read_time > 0 else 0
            )
        )
        print(
            "  | {:^15} | {:^12.2f} | {:^15.1f} |".format(
                "Alter", alter_time, NUM_UPDATES / alter_time if alter_time > 0 else 0
            )
        )
        print(
            "  | {:^15} | {:^12.2f} | {:^15.1f} |".format(
                "Dump", dump_time, NUM_ENTRIES / dump_time if dump_time > 0 else 0
            )
        )
        print("  " + "-" * 48)

        print("\n" + "=" * 50)

    def define(self) -> Operation:
        """Define the benchmark sequence."""
        return self.ex.Sequence(
            # Setup
            self.ex.Function(self.setup),
            # Phase 1: Populate
            self.ex.Function(self.populate_storage),
            # Phase 2: Read
            self.ex.Function(self.read_storage),
            # Phase 3: Alter
            self.ex.Function(self.alter_storage),
            # Phase 4: Dump
            self.ex.Function(self.dump_storage),
            # Final report
            self.ex.Function(self.print_report),
            error_behavior="fail",
            on_fail=self.ex.Sequence(
                self.ex.Function(self.dump_storage),
                self.ex.Function(self.print_report),
            ),
        )


async def main():
    print("\n" + "=" * 50)
    print("STARTING KV STORAGE BENCHMARK")
    print("=" * 50)
    print(f"Storage type: {'LMDB' if USE_LMDB else 'In-Memory'}")
    print(f"Number of entries: {NUM_ENTRIES:,}")
    print(f"Number of updates: {NUM_UPDATES:,}")
    print(f"Batch size: {BATCH_SIZE:,}")
    print("=" * 50)

    start_time = time.time()

    async with BenchmarkApp(
        state_spec=state_spec,
        executor_spec=executor_spec,
    ) as app:
        await app.start()

    total_time = time.time() - start_time
    print(f"\nBenchmark completed in {total_time:.2f} seconds\n")


if __name__ == "__main__":
    asyncio.run(main())
