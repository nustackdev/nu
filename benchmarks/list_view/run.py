"""
State v3 ListView Benchmark Tool

This benchmarks the ListView interface with three key operations:
1. Append: Add items to the end of the list
2. Get: Retrieve items by index (sequential, random, and repeated patterns)
3. Pop: Remove items from the end of the list

Tests the LMDB storage backend with ListView operations.
"""

import random
import statistics
import time
from pathlib import Path

from loomistd.specs import LMDBStorageSpec, SyncStateSpec
from loomistd.state import StateService

# Constants
NUM_ENTRIES = 50_000  # Reduced from dict benchmark since lists have more overhead
NUM_GETS = 1000
NUM_POPS = 5_000  # Pop a portion of the appended items
BATCH_SIZE = 250  # Smaller batches for list operations
GET_PATTERNS = ["sequential", "random", "repeated"]  # Different get patterns to benchmark

# Storage configuration
STORAGE_CONFIG = SyncStateSpec(storage=LMDBStorageSpec()).with_value_at(
    "storage", "path", value=".benchmark_listview_lmdb"
)


class ListViewBenchmark:
    def __init__(self):
        self.storage_name = "LMDB ListView"
        self.metrics = {
            "append": {"start": 0, "end": 0, "batches": []},
            "get": {"start": 0, "end": 0, "batches": [], "patterns": {}},
            "pop": {"start": 0, "end": 0, "batches": []},
        }

        # Initialize metrics for each get pattern
        for pattern in GET_PATTERNS:
            self.metrics["get"]["patterns"][pattern] = {
                "start": 0,
                "end": 0,
                "batches": [],
                "success_count": 0,
                "error_count": 0,
            }

    def create_state_spec(self) -> SyncStateSpec:
        """Create state specification for LMDB storage."""
        return STORAGE_CONFIG

    def append_items(self, state):
        """Append items to the list."""
        self.metrics["append"]["start"] = time.time()
        print(f"\n[{time.strftime('%H:%M:%S')}] Starting append phase...")

        # Process in batches
        for batch_idx in range(0, NUM_ENTRIES, BATCH_SIZE):
            batch_start = time.time()

            with state.at("benchmark_list").with_list_view() as data:
                # Append batch of random values
                for i in range(batch_idx, min(batch_idx + BATCH_SIZE, NUM_ENTRIES)):
                    value = f"item_{i}_{random.randint(1, 10000)}"
                    data.append(value)

            batch_time = time.time() - batch_start
            self.metrics["append"]["batches"].append(batch_time)

            # Progress update every 20 batches
            if (batch_idx // BATCH_SIZE) % 20 == 0:
                progress = min(100, (batch_idx + BATCH_SIZE) * 100 // NUM_ENTRIES)
                print(f"  Append {progress}% complete, batch time: {batch_time:.4f}s")

        self.metrics["append"]["end"] = time.time()
        total_time = self.metrics["append"]["end"] - self.metrics["append"]["start"]
        print(f"[{time.strftime('%H:%M:%S')}] Append complete in {total_time:.2f}s")

        # Verify list length
        with state.at("benchmark_list").with_list_view() as data:
            length = data.length()
            print(f"  Verified list length: {length}")

    def get_items(self, state):  # noqa: C901
        """Benchmark different get patterns."""
        self.metrics["get"]["start"] = time.time()
        print(f"\n[{time.strftime('%H:%M:%S')}] Starting get phase...")

        # Get current list length
        with state.at("benchmark_list").with_list_view() as data:
            list_length = data.length()

        print(f"  Current list length: {list_length}")

        # Test different get patterns
        for pattern in GET_PATTERNS:
            print(f"  Testing '{pattern}' get pattern...")
            self.metrics["get"]["patterns"][pattern]["start"] = time.time()
            success_count, error_count = 0, 0

            if pattern == "sequential":
                # Sequential gets from start to end
                for batch_idx in range(0, NUM_GETS, BATCH_SIZE):
                    batch_start = time.time()

                    with state.at("benchmark_list").with_list_view() as data:
                        for i in range(batch_idx, min(batch_idx + BATCH_SIZE, NUM_GETS)):
                            index = i % list_length  # Wrap around if needed
                            try:
                                value = data.get(index)
                                if value is not None:
                                    success_count += 1
                                else:
                                    error_count += 1
                            except Exception:
                                error_count += 1

                    batch_time = time.time() - batch_start
                    self.metrics["get"]["patterns"][pattern]["batches"].append(batch_time)

                    # Progress update
                    if (batch_idx // BATCH_SIZE) % 10 == 0:
                        progress = min(100, (batch_idx + BATCH_SIZE) * 100 // NUM_GETS)
                        print(f"    {progress}% complete, batch time: {batch_time:.4f}s")

            elif pattern == "random":
                # Random gets
                for batch_idx in range(0, NUM_GETS, BATCH_SIZE):
                    batch_start = time.time()

                    with state.at("benchmark_list").with_list_view() as data:
                        for i in range(batch_idx, min(batch_idx + BATCH_SIZE, NUM_GETS)):
                            # Mix of valid and potentially invalid indices
                            if random.random() < 0.8:  # 80% valid indices
                                index = random.randint(0, list_length - 1)
                            else:  # 20% potentially invalid indices
                                index = random.randint(list_length, list_length + 1000)

                            try:
                                value = data.get(index)
                                if value is not None:
                                    success_count += 1
                                else:
                                    error_count += 1
                            except Exception:
                                error_count += 1

                    batch_time = time.time() - batch_start
                    self.metrics["get"]["patterns"][pattern]["batches"].append(batch_time)

                    # Progress update
                    if (batch_idx // BATCH_SIZE) % 10 == 0:
                        progress = min(100, (batch_idx + BATCH_SIZE) * 100 // NUM_GETS)
                        print(f"    {progress}% complete, batch time: {batch_time:.4f}s")

            elif pattern == "repeated":
                # Repeated gets of hot indices (simulates cache behavior)
                hot_indices = [random.randint(0, min(list_length - 1, 99)) for _ in range(10)]

                for batch_idx in range(0, NUM_GETS, BATCH_SIZE):
                    batch_start = time.time()

                    with state.at("benchmark_list").with_list_view() as data:
                        for i in range(batch_idx, min(batch_idx + BATCH_SIZE, NUM_GETS)):
                            # 80% hot indices, 20% random indices
                            if random.random() < 0.8:
                                index = random.choice(hot_indices)
                            else:
                                index = random.randint(0, list_length - 1)

                            try:
                                value = data.get(index)
                                if value is not None:
                                    success_count += 1
                                else:
                                    error_count += 1
                            except Exception:
                                error_count += 1

                    batch_time = time.time() - batch_start
                    self.metrics["get"]["patterns"][pattern]["batches"].append(batch_time)

                    # Progress update
                    if (batch_idx // BATCH_SIZE) % 10 == 0:
                        progress = min(100, (batch_idx + BATCH_SIZE) * 100 // NUM_GETS)
                        print(f"    {progress}% complete, batch time: {batch_time:.4f}s")

            # Calculate success/error rates
            total = success_count + error_count
            success_rate = (success_count / total) * 100 if total > 0 else 0
            error_rate = (error_count / total) * 100 if total > 0 else 0

            self.metrics["get"]["patterns"][pattern]["success_count"] = success_count
            self.metrics["get"]["patterns"][pattern]["error_count"] = error_count
            self.metrics["get"]["patterns"][pattern]["end"] = time.time()

            pattern_time = (
                self.metrics["get"]["patterns"][pattern]["end"]
                - self.metrics["get"]["patterns"][pattern]["start"]
            )
            print(
                f"    '{pattern}' complete in {pattern_time:.2f}s, success rate: {success_rate:.1f}%, error rate: {error_rate:.1f}%"
            )

        # Overall get phase timing
        self.metrics["get"]["end"] = time.time()
        total_time = self.metrics["get"]["end"] - self.metrics["get"]["start"]
        print(f"[{time.strftime('%H:%M:%S')}] Get phase complete in {total_time:.2f}s")

    def pop_items(self, state):
        """Pop items from the end of the list."""
        self.metrics["pop"]["start"] = time.time()
        print(f"\n[{time.strftime('%H:%M:%S')}] Starting pop phase...")

        # Get initial length
        with state.at("benchmark_list").with_list_view() as data:
            initial_length = data.length()

        print(f"  Initial list length: {initial_length}")

        # Process pops in batches
        for batch_idx in range(0, NUM_POPS, BATCH_SIZE):
            batch_start = time.time()

            with state.at("benchmark_list").with_list_view() as data:
                # Pop items from the batch
                batch_end = min(batch_idx + BATCH_SIZE, NUM_POPS)
                for i in range(batch_idx, batch_end):
                    try:
                        if data.length() > 0:  # Check if list is not empty
                            data.pop()
                        else:
                            break  # Stop if list is empty
                    except Exception:
                        # List might be empty, break
                        break

            batch_time = time.time() - batch_start
            self.metrics["pop"]["batches"].append(batch_time)

            # Progress update every 20 batches
            if (batch_idx // BATCH_SIZE) % 20 == 0:
                progress = min(100, (batch_idx + BATCH_SIZE) * 100 // NUM_POPS)
                with state.at("benchmark_list").with_list_view() as data:
                    current_length = data.length()
                print(
                    f"  Pop {progress}% complete, batch time: {batch_time:.4f}s, remaining: {current_length}"
                )

        self.metrics["pop"]["end"] = time.time()
        total_time = self.metrics["pop"]["end"] - self.metrics["pop"]["start"]
        print(f"[{time.strftime('%H:%M:%S')}] Pop complete in {total_time:.2f}s")

        # Verify final length
        with state.at("benchmark_list").with_list_view() as data:
            final_length = data.length()
            popped_count = initial_length - final_length
            print(f"  Final list length: {final_length}")
            print(f"  Successfully popped: {popped_count} items")

    def print_report(self):
        """Print performance report."""
        print("\n" + "=" * 60)
        print("LISTVIEW BENCHMARK PERFORMANCE REPORT")
        print("=" * 60)

        print(f"Storage Type: {self.storage_name}")
        print(f"Append Operations: {NUM_ENTRIES:,}")
        print(f"Get Operations: {NUM_GETS:,} per pattern")
        print(f"Pop Operations: {NUM_POPS:,}")
        print(f"Batch Size: {BATCH_SIZE:,}")

        total_time = sum(
            [
                self.metrics["append"]["end"] - self.metrics["append"]["start"],
                self.metrics["get"]["end"] - self.metrics["get"]["start"],
                self.metrics["pop"]["end"] - self.metrics["pop"]["start"],
            ]
        )

        print("\nTiming Results:")
        print(f"  Total benchmark time: {total_time:.2f}s")

        # Append and Pop phases
        for phase in ["append", "pop"]:
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

            total_ops = NUM_ENTRIES if phase == "append" else NUM_POPS
            ops_per_sec = total_ops / phase_time if phase_time > 0 else 0
            print(f"    Operations per second: {ops_per_sec:.1f}")

        # Get phase (with patterns)
        print("\n  Get phase:")
        get_time = self.metrics["get"]["end"] - self.metrics["get"]["start"]
        print(f"    Total time: {get_time:.2f}s")

        # Print details for each get pattern
        for pattern in GET_PATTERNS:
            pattern_data = self.metrics["get"]["patterns"][pattern]
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
            print(f"      Successful gets: {pattern_data['success_count']}")
            print(f"      Failed gets: {pattern_data['error_count']}")

            ops_per_sec = NUM_GETS / pattern_time if pattern_time > 0 else 0
            print(f"      Operations per second: {ops_per_sec:.1f}")

        # Summary table
        print("\n  Performance Summary:")
        print("  " + "-" * 48)
        print("  | {:^15} | {:^12} | {:^15} |".format("Operation", "Time (s)", "Ops/sec"))
        print("  " + "-" * 48)

        # Add each phase to the summary
        append_time = self.metrics["append"]["end"] - self.metrics["append"]["start"]
        get_time = self.metrics["get"]["end"] - self.metrics["get"]["start"]
        pop_time = self.metrics["pop"]["end"] - self.metrics["pop"]["start"]

        print(
            "  | {:^15} | {:^12.2f} | {:^15.1f} |".format(
                "Append", append_time, NUM_ENTRIES / append_time if append_time > 0 else 0
            )
        )
        print(
            "  | {:^15} | {:^12.2f} | {:^15.1f} |".format(
                "Get", get_time, NUM_GETS * 3 / get_time if get_time > 0 else 0
            )
        )
        print(
            "  | {:^15} | {:^12.2f} | {:^15.1f} |".format(
                "Pop", pop_time, NUM_POPS / pop_time if pop_time > 0 else 0
            )
        )
        print("  " + "-" * 48)

        print("=" * 60)

    def run_benchmark(self):
        """Run the complete ListView benchmark."""
        print(f"\n{'=' * 60}")
        print("STARTING LISTVIEW STORAGE BENCHMARK")
        print(f"{'=' * 60}")
        print(f"Storage type: {self.storage_name}")
        print(f"Number of appends: {NUM_ENTRIES:,}")
        print(f"Number of gets per pattern: {NUM_GETS:,}")
        print(f"Number of pops: {NUM_POPS:,}")
        print(f"Batch size: {BATCH_SIZE:,}")
        print(f"{'=' * 60}")

        start_time = time.time()

        try:
            state_spec = self.create_state_spec()

            with StateService(state_spec) as state_service:
                state = state_service.state

                # Phase 1: Append
                self.append_items(state)

                # Phase 2: Get
                self.get_items(state)

                # Phase 3: Pop
                self.pop_items(state)

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

        # Clean up database files
        import shutil

        for path in [".benchmark_listview_lmdb"]:
            try:
                if Path(path).exists():
                    if Path(path).is_dir():
                        shutil.rmtree(path)
                    else:
                        Path(path).unlink()
            except Exception:
                pass

        return self.metrics


def main():
    """Main entry point."""
    benchmark = ListViewBenchmark()
    benchmark.run_benchmark()


if __name__ == "__main__":
    main()
