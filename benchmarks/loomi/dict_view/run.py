"""
State v3 Storage Benchmark Tool

This benchmarks the new state v3 key-value storage system with four phases:
1. Populate: Fill storage with random numbers
2. Read: Perform random reads to test retrieval performance
3. Alter: Perform random updates to test write performance
4. Dump: Clear all storage and measure cleanup performance

Tests all three storage backends: InMemory, LMDB, and SyncFile
"""

import random
import statistics
import time
from pathlib import Path

from loomistd.specs import LMDBStorageSpec, SyncStateSpec
from loomistd.state import StateService

# Constants
NUM_ENTRIES = 100_000
NUM_READS = 1000
NUM_UPDATES = 1000
BATCH_SIZE = 500  # Process in batches for better performance
READ_PATTERNS = ["sequential", "random", "repeated"]  # Different read patterns to benchmark

# Storage configurations to test
STORAGE_CONFIGS = {
    # "InMemory": lambda: StateSpec(storage=InMemoryStorageSpec()),
    "LMDB": lambda: SyncStateSpec(storage=LMDBStorageSpec()).with_value_at(
        "storage", "path", value=".benchmark_lmdb"
    ),
    # "SyncFile": lambda: StateSpec(storage=SyncFileStorageSpec()).with_value_at(
    #     "storage", "path", value=".benchmark_syncfile"
    # ),
}


class StateV3Benchmark:
    def __init__(self, storage_name: str):
        self.storage_name = storage_name
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

    def create_state_spec(self) -> SyncStateSpec:
        """Create state specification based on storage type."""
        return STORAGE_CONFIGS[self.storage_name]()

    def populate_storage(self, state):
        """Populate storage with random numbers."""
        self.metrics["populate"]["start"] = time.time()
        print(f"\n[{time.strftime('%H:%M:%S')}] Starting population phase...")

        # Process in batches
        for batch_idx in range(0, NUM_ENTRIES, BATCH_SIZE):
            batch_start = time.time()

            with state.at("benchmark_data").with_dict_view() as data:
                # Generate and store batch of random numbers
                for i in range(batch_idx, min(batch_idx + BATCH_SIZE, NUM_ENTRIES)):
                    key = f"key_{i}"
                    value = random.randint(1, 10000)
                    data.set(key, value)

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
        # count = self._count_items(state)
        # print(f"  Verified {count} items in storage")

    def read_storage(self, state):  # noqa: C901
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

                    with state.at("benchmark_data").with_dict_view() as data:
                        for i in range(batch_idx, min(batch_idx + BATCH_SIZE, NUM_READS)):
                            key = f"key_{i % NUM_ENTRIES}"
                            try:
                                value = data.get(key)
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

                    with state.at("benchmark_data").with_dict_view() as data:
                        for i in range(batch_idx, min(batch_idx + BATCH_SIZE, NUM_READS)):
                            key = f"key_{random.randint(0, NUM_ENTRIES * 2)}"  # Include some out-of-range keys
                            try:
                                value = data.get(key)
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

                    with state.at("benchmark_data").with_dict_view() as data:
                        for i in range(batch_idx, min(batch_idx + BATCH_SIZE, NUM_READS)):
                            # 80% hot keys, 20% random keys
                            if random.random() < 0.8:
                                key = random.choice(hot_keys)
                            else:
                                key = f"key_{random.randint(0, NUM_ENTRIES - 1)}"

                            try:
                                value = data.get(key)
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

    def alter_storage(self, state):
        """Randomly update entries."""
        self.metrics["alter"]["start"] = time.time()
        print(f"\n[{time.strftime('%H:%M:%S')}] Starting alteration phase...")

        # Process updates in batches
        for batch_idx in range(0, NUM_UPDATES, BATCH_SIZE):
            batch_start = time.time()

            with state.at("benchmark_data").with_dict_view() as data:
                # Perform random updates
                for i in range(batch_idx, min(batch_idx + BATCH_SIZE, NUM_UPDATES)):
                    key = f"key_{random.randint(0, NUM_ENTRIES - 1)}"
                    value = random.randint(1, 10000)
                    data.set(key, value)

            batch_time = time.time() - batch_start
            self.metrics["alter"]["batches"].append(batch_time)

            # Progress update every 10 batches
            if (batch_idx // BATCH_SIZE) % 10 == 0:
                progress = min(100, (batch_idx + BATCH_SIZE) * 100 // NUM_UPDATES)
                print(f"  Alteration {progress}% complete, batch time: {batch_time:.4f}s")

        self.metrics["alter"]["end"] = time.time()
        total_time = self.metrics["alter"]["end"] - self.metrics["alter"]["start"]
        print(f"[{time.strftime('%H:%M:%S')}] Alteration complete in {total_time:.2f}s")

    def dump_storage(self, state):
        """Clear all storage."""
        self.metrics["dump"]["start"] = time.time()
        print(f"\n[{time.strftime('%H:%M:%S')}] Starting dump phase...")

        # Count items before clearing
        count_before = self._count_items(state)
        print(f"  Items before dump: {count_before}")

        # Process deletion in batches
        for batch_idx in range(0, NUM_ENTRIES, BATCH_SIZE):
            batch_start = time.time()

            with state.at("benchmark_data").with_dict_view() as data:
                # Delete batch of keys - trying different possible methods
                for i in range(batch_idx, min(batch_idx + BATCH_SIZE, NUM_ENTRIES)):
                    key = f"key_{i}"
                    try:
                        # Try different deletion methods
                        if hasattr(data, "remove"):
                            data.remove(key)
                        elif hasattr(data, "delete"):
                            data.delete(key)
                        else:
                            # Fallback: set to None or empty value
                            data.set(key, None)
                    except Exception:
                        # Key might not exist, continue
                        pass

            batch_time = time.time() - batch_start
            self.metrics["dump"]["batches"].append(batch_time)

            # Progress update every 10 batches
            if (batch_idx // BATCH_SIZE) % 10 == 0:
                progress = min(100, (batch_idx + BATCH_SIZE) * 100 // NUM_ENTRIES)
                print(f"  Dump {progress}% complete, batch time: {batch_time:.4f}s")

        # Verify storage cleanup
        count_after = self._count_items(state)
        print(f"  Items after dump: {count_after}")

        self.metrics["dump"]["end"] = time.time()
        total_time = self.metrics["dump"]["end"] - self.metrics["dump"]["start"]
        print(f"[{time.strftime('%H:%M:%S')}] Dump complete in {total_time:.2f}s")

    def _count_items(self, state) -> int:
        """Helper to count items in storage."""
        try:
            with state.at("benchmark_data").with_dict_view() as data:
                # Try different ways to count items
                if hasattr(data, "__len__"):
                    return len(data)
                elif hasattr(data, "keys"):
                    return len(list(data.keys()))
                else:
                    # Fallback: try to count by iterating
                    count = 0
                    try:
                        for _ in data:
                            count += 1
                    except Exception:
                        # If iteration doesn't work, return 0
                        pass
                    return count
        except Exception:
            return 0

    def print_report(self):
        """Print performance report."""
        print("\n" + "=" * 60)
        print(f"STATE V3 BENCHMARK PERFORMANCE REPORT - {self.storage_name}")
        print("=" * 60)

        print(f"Storage Type: {self.storage_name}")
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

        print("=" * 60)

    def run_benchmark(self):
        """Run the complete benchmark."""
        print(f"\n{'=' * 60}")
        print(f"STARTING STATE V3 STORAGE BENCHMARK - {self.storage_name}")
        print(f"{'=' * 60}")
        print(f"Storage type: {self.storage_name}")
        print(f"Number of entries: {NUM_ENTRIES:,}")
        print(f"Number of updates: {NUM_UPDATES:,}")
        print(f"Batch size: {BATCH_SIZE:,}")
        print(f"{'=' * 60}")

        start_time = time.time()

        try:
            state_spec = self.create_state_spec()

            with StateService(state_spec) as state_service:
                state = state_service.state

                # Phase 1: Populate
                self.populate_storage(state)

                # Phase 2: Read
                self.read_storage(state)

                # Phase 3: Alter
                self.alter_storage(state)

                # Phase 4: Dump
                self.dump_storage(state)

        except Exception as e:
            print(f"Benchmark failed with error: {e}")
            print("Attempting to print partial results...")
            import traceback

            traceback.print_exc()
        finally:
            # Always print report, even if benchmark failed
            self.print_report()

        total_time = time.time() - start_time
        print(f"\nBenchmark completed in {total_time:.2f} seconds\n")

        return self.metrics


def run_all_benchmarks():
    """Run benchmarks for all storage types and compare results."""
    print("\n" + "=" * 80)
    print("COMPREHENSIVE STATE V3 STORAGE COMPARISON")
    print("=" * 80)

    all_results = {}

    for storage_name in STORAGE_CONFIGS.keys():
        print(f"\n\n{'*' * 20} Testing {storage_name} Storage {'*' * 20}")

        benchmark = StateV3Benchmark(storage_name)
        metrics = benchmark.run_benchmark()
        all_results[storage_name] = metrics

        # Clean up any database files between tests
        import shutil

        for path in [".benchmark_lmdb", ".benchmark_syncfile"]:
            try:
                if Path(path).exists():
                    if Path(path).is_dir():
                        shutil.rmtree(path)
                    else:
                        Path(path).unlink()
            except Exception:
                pass

    # Print comparison summary
    print_comparison_summary(all_results)


def print_comparison_summary(results):
    """Print a comparison summary of all storage backends."""
    print("\n" + "=" * 80)
    print("STORAGE BACKEND COMPARISON SUMMARY")
    print("=" * 80)

    # Extract key metrics for comparison
    comparison_data = {}

    for storage_name, metrics in results.items():
        comparison_data[storage_name] = {
            "populate_time": metrics["populate"]["end"] - metrics["populate"]["start"],
            "read_time": metrics["read"]["end"] - metrics["read"]["start"],
            "alter_time": metrics["alter"]["end"] - metrics["alter"]["start"],
            "dump_time": metrics["dump"]["end"] - metrics["dump"]["start"],
        }

        # Calculate total time
        comparison_data[storage_name]["total_time"] = sum(comparison_data[storage_name].values())

        # Calculate ops/sec
        for phase, ops_count in [("populate", NUM_ENTRIES), ("alter", NUM_UPDATES)]:
            time_taken = comparison_data[storage_name][f"{phase}_time"]
            comparison_data[storage_name][f"{phase}_ops_per_sec"] = (
                ops_count / time_taken if time_taken > 0 else 0
            )

        # Read ops/sec (total across all patterns)
        read_time = comparison_data[storage_name]["read_time"]
        comparison_data[storage_name]["read_ops_per_sec"] = (
            (NUM_READS * 3) / read_time if read_time > 0 else 0
        )

    # Print comparison table
    print("\nPerformance Comparison:")
    print("-" * 120)
    header = f"{'Storage':<12} | {'Populate':<12} | {'Read':<12} | {'Alter':<12} | {'Dump':<12} | {'Total':<12} | {'Pop/s':<12} | {'Read/s':<12} | {'Alt/s':<12}"
    print(header)
    print("-" * 120)

    for storage_name, data in comparison_data.items():
        row = f"{storage_name:<12} | {data['populate_time']:<12.2f} | {data['read_time']:<12.2f} | {data['alter_time']:<12.2f} | {data['dump_time']:<12.2f} | {data['total_time']:<12.2f} | {data['populate_ops_per_sec']:<12.0f} | {data['read_ops_per_sec']:<12.0f} | {data['alter_ops_per_sec']:<12.0f}"
        print(row)

    print("-" * 120)

    # Find winners in each category
    print("\nPerformance Winners:")
    categories = [
        ("Fastest Populate", "populate_time", False),
        ("Fastest Read", "read_time", False),
        ("Fastest Alter", "alter_time", False),
        ("Fastest Dump", "dump_time", False),
        ("Fastest Overall", "total_time", False),
        ("Highest Populate Ops/sec", "populate_ops_per_sec", True),
        ("Highest Read Ops/sec", "read_ops_per_sec", True),
        ("Highest Alter Ops/sec", "alter_ops_per_sec", True),
    ]

    for category_name, metric_key, higher_is_better in categories:
        if higher_is_better:
            winner = max(comparison_data.items(), key=lambda x: x[1][metric_key])
        else:
            winner = min(comparison_data.items(), key=lambda x: x[1][metric_key])

        storage_name, data = winner
        value = data[metric_key]
        unit = "ops/sec" if "ops_per_sec" in metric_key else "seconds"
        print(f"  {category_name}: {storage_name} ({value:.2f} {unit})")

    print("=" * 80)


def main():
    """Main entry point."""
    run_all_benchmarks()


if __name__ == "__main__":
    main()
