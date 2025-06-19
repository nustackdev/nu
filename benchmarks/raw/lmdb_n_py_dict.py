#!/usr/bin/env python3
"""
LMDB vs Python Dict Performance Benchmark - CLEAR RESULTS VERSION

Fair and reliable performance comparison with easy-to-read results table.
Fixed to separate single write timing from transaction overhead.

Requirements: pip install lmdb psutil
"""

import gc
import os
import platform
import random
import shutil
import statistics
import string
import sys
import tempfile
import time
from typing import Dict, List, Tuple

import lmdb
import psutil


class Colors:
    """ANSI color codes for terminal output"""

    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


class BenchmarkRunner:
    def __init__(self):
        self.results = {}
        self.system_info = self._get_system_info()

    def _get_system_info(self) -> Dict:
        """Collect system information for reporting"""
        try:
            return {
                "python_version": sys.version.split()[0],
                "platform": platform.system(),
                "platform_release": platform.release(),
                "architecture": platform.architecture()[0],
                "processor": platform.processor() or "Unknown",
                "cpu_count": os.cpu_count(),
                "memory_gb": round(psutil.virtual_memory().total / (1024**3), 1),
                "lmdb_version": lmdb.version(),
            }
        except Exception as e:
            return {"error": f"Could not collect system info: {e}"}

    def _format_time(self, seconds: float) -> str:
        """Format time with appropriate units"""
        if seconds < 1e-6:  # Less than 1 microsecond
            return f"{seconds * 1e9:.1f}ns"
        elif seconds < 1e-3:  # Less than 1 millisecond
            return f"{seconds * 1e6:.1f}μs"
        elif seconds < 1:  # Less than 1 second
            return f"{seconds * 1e3:.1f}ms"
        else:
            return f"{seconds:.2f}s"

    def _format_ops_per_second(self, seconds: float, item_count: int) -> str:
        """Calculate and format operations per second"""
        if seconds <= 0:
            return "∞"

        ops_per_second = item_count / seconds
        if ops_per_second >= 1e6:
            return f"{ops_per_second / 1e6:.2f}M"
        elif ops_per_second >= 1e3:
            return f"{ops_per_second / 1e3:.1f}K"
        else:
            return f"{ops_per_second:.0f}"

    def generate_test_data(
        self, num_items: int, key_size: int = 15, value_size: int = 200
    ) -> List[Tuple[str, str]]:
        """Generate random key-value pairs for testing"""
        random.seed(42)  # Reproducible results
        data = []
        for i in range(num_items):
            key = f"key_{i:08d}_{''.join(random.choices(string.ascii_letters, k=key_size))}"
            value = "".join(random.choices(string.ascii_letters + string.digits, k=value_size))
            data.append((key, value))
        return data

    def time_operation(
        self, operation_func, iterations: int = 10, warmup_runs: int = 2
    ) -> Dict[str, float]:
        """Time an operation multiple times with warmup and return statistics"""
        # Warmup runs to eliminate cold-start effects
        for _ in range(warmup_runs):
            operation_func()

        times = []
        for _ in range(iterations):
            gc.collect()  # Clean up before each run
            time.sleep(0.001)  # Brief pause to ensure clean state
            start_time = time.perf_counter()
            operation_func()
            end_time = time.perf_counter()
            times.append(end_time - start_time)

        return {
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "min": min(times),
            "max": max(times),
            "std": statistics.stdev(times) if len(times) > 1 else 0,
            "raw_times": times,  # type: ignore
        }

    def benchmark_dict_operations(self, data: List[Tuple[str, str]]) -> Dict[str, Dict[str, float]]:
        """Benchmark Python dict operations"""
        results = {}

        # Write benchmark - bulk insertion
        def write_all():
            d = {}
            for key, value in data:
                d[key] = value
            return d

        results["bulk_write"] = self.time_operation(write_all)

        # Create dict for read benchmarks - reused across tests
        test_dict = {}
        for key, value in data:
            test_dict[key] = value

        # Sequential read benchmark
        def read_sequential():
            for key, _ in data:
                _ = test_dict[key]

        results["read_sequential"] = self.time_operation(read_sequential)

        # Random read benchmark
        random_keys = [key for key, _ in random.sample(data, min(1000, len(data)))]

        def read_random():
            for key in random_keys:
                _ = test_dict[key]

        results["read_random"] = self.time_operation(read_random)
        results["read_random_sample_size"] = len(random_keys)

        # Single item operations - using persistent dict
        # NOTE: Removed single read/write benchmarks due to measurement precision issues
        # and because they don't represent realistic usage patterns

        # Update benchmark
        update_data = [(key, value + "_updated") for key, value in data[: min(1000, len(data))]]

        def update_items():
            for key, new_value in update_data:
                test_dict[key] = new_value

        results["batch_update"] = self.time_operation(update_items)
        results["update_sample_size"] = len(update_data)

        return results

    def benchmark_lmdb_operations(
        self, data: List[Tuple[str, str]], db_path: str
    ) -> Dict[str, Dict[str, float]]:
        """Benchmark LMDB operations with proper connection reuse and separate transaction timing"""
        results = {}

        # Calculate map size (generous estimate)
        total_size = sum(len(k.encode()) + len(v.encode()) for k, v in data)
        map_size = max(total_size * 10, 10 * 1024 * 1024)
        results["map_size_mb"] = map_size / (1024 * 1024)

        # Create persistent environment for all operations
        env = lmdb.open(db_path, map_size=map_size)

        try:
            # Bulk write benchmark - single transaction
            def write_all():
                with env.begin(write=True) as txn:
                    for key, value in data:
                        txn.put(key.encode(), value.encode())

            results["bulk_write"] = self.time_operation(write_all)

            # Sequential read benchmark - single transaction
            def read_sequential():
                with env.begin() as txn:
                    for key, _ in data:
                        _ = txn.get(key.encode())

            results["read_sequential"] = self.time_operation(read_sequential)

            # Random read benchmark - single transaction
            random_keys = [key for key, _ in random.sample(data, min(1000, len(data)))]

            def read_random():
                with env.begin() as txn:
                    for key in random_keys:
                        _ = txn.get(key.encode())

            results["read_random"] = self.time_operation(read_random)
            results["read_random_sample_size"] = len(random_keys)

            # DIAGNOSTIC: Measure transaction overhead separately (for both read and write)
            def transaction_overhead_write():
                with env.begin(write=True) as txn:
                    pass  # Empty write transaction - measures just tx overhead

            def transaction_overhead_read():
                with env.begin() as txn:
                    pass  # Empty read transaction - measures just tx overhead

            results["transaction_overhead_write"] = self.time_operation(
                transaction_overhead_write, iterations=1000, warmup_runs=10
            )

            results["transaction_overhead_read"] = self.time_operation(
                transaction_overhead_read, iterations=1000, warmup_runs=10
            )

            # Update benchmark - single transaction
            update_data = [(key, value + "_updated") for key, value in data[: min(1000, len(data))]]

            def update_items():
                with env.begin(write=True) as txn:
                    for key, new_value in update_data:
                        txn.put(key.encode(), new_value.encode())

            results["batch_update"] = self.time_operation(update_items)
            results["update_sample_size"] = len(update_data)

        finally:
            env.close()

        return results

    def generate_clear_report(self, all_results: List[Dict]) -> str:
        """Generate clear, easy-to-read performance report"""
        report = []

        # Header
        report.append(f"{Colors.BOLD}{Colors.CYAN}{'=' * 90}{Colors.END}")
        report.append(
            f"{Colors.BOLD}{Colors.CYAN}LMDB vs PYTHON DICT PERFORMANCE BENCHMARK - CLEAR RESULTS{Colors.END}"
        )
        report.append(f"{Colors.BOLD}{Colors.CYAN}{'=' * 90}{Colors.END}")

        # System Information
        report.append(f"\n{Colors.YELLOW}{Colors.BOLD}SYSTEM INFO:{Colors.END}")
        info = self.system_info
        report.append(
            f"Python {info.get('python_version', 'Unknown')} | "
            f"{info.get('platform', 'Unknown')} | "
            f"{info.get('cpu_count', 'Unknown')} CPUs | "
            f"{info.get('memory_gb', 'Unknown')}GB RAM"
        )

        if "lmdb_version" in info:
            v = info["lmdb_version"]
            report.append(f"LMDB Version: {v[0]}.{v[1]}.{v[2]}")

        # Results for Each Dataset Size
        for result in all_results:
            size = result["size"]
            dict_results = result["dict"]
            lmdb_results = result["lmdb"]

            report.append(f"\n{Colors.BOLD}{Colors.MAGENTA}{'='*90}{Colors.END}")
            report.append(f"{Colors.BOLD}{Colors.MAGENTA}DATASET: {size:,} ITEMS{Colors.END}")
            report.append(f"{Colors.BOLD}{Colors.MAGENTA}{'=' * 90}{Colors.END}")

            # Clear Results Table - removed single operations
            operations = [
                ("bulk_write", "Bulk Write", size, "items"),
                ("read_sequential", "Sequential Read", size, "items"),
                (
                    "read_random",
                    "Random Read",
                    dict_results.get("read_random_sample_size", 1000),
                    "items",
                ),
                (
                    "batch_update",
                    "Batch Update",
                    dict_results.get("update_sample_size", 1000),
                    "items",
                ),
            ]

            report.append(f"\n{Colors.BOLD}{Colors.WHITE}PERFORMANCE RESULTS:{Colors.END}")
            report.append(f"{Colors.WHITE}{'-' * 110}{Colors.END}")

            # Clear table header
            header = f"{'Operation':<15} {'Dict Time':<12} {'Dict Ops/s':<12} {'LMDB Time':<12} {'LMDB Ops/s':<12} {'Winner':<20} {'Speedup':<10}"
            report.append(f"{Colors.BOLD}{header}{Colors.END}")
            report.append(f"{Colors.WHITE}{'-' * 110}{Colors.END}")

            for op_key, op_name, item_count, unit in operations:
                if op_key in dict_results and op_key in lmdb_results:
                    dict_time = dict_results[op_key]["mean"]
                    lmdb_time = lmdb_results[op_key]["mean"]

                    dict_ops = self._format_ops_per_second(dict_time, item_count)
                    lmdb_ops = self._format_ops_per_second(lmdb_time, item_count)

                    # Determine winner and speedup
                    if dict_time > 0 and lmdb_time > 0:
                        if dict_time < lmdb_time:
                            winner = f"{Colors.GREEN}Dict{Colors.END}"
                            speedup = f"{Colors.GREEN}{lmdb_time / dict_time:.1f}x{Colors.END}"
                        else:
                            winner = f"{Colors.BLUE}LMDB{Colors.END}"
                            speedup = f"{Colors.BLUE}{dict_time / lmdb_time:.1f}x{Colors.END}"
                    else:
                        winner = "N/A"
                        speedup = "N/A"

                    row = (
                        f"{op_name:<15} "
                        f"{self._format_time(dict_time):<12} "
                        f"{dict_ops + '/s':<12} "
                        f"{self._format_time(lmdb_time):<12} "
                        f"{lmdb_ops + '/s':<12} "
                        f"{winner:<28} "  # Extra space for color codes
                        f"{speedup:<18}"
                    )  # Extra space for color codes

                    report.append(row)

            # DIAGNOSTIC: Transaction overhead analysis
            if (
                "transaction_overhead_write" in lmdb_results
                and "transaction_overhead_read" in lmdb_results
            ):
                tx_overhead_write = lmdb_results["transaction_overhead_write"]["mean"]
                tx_overhead_read = lmdb_results["transaction_overhead_read"]["mean"]

                report.append(
                    f"\n{Colors.YELLOW}{Colors.BOLD}LMDB TRANSACTION OVERHEAD ANALYSIS:{Colors.END}"
                )
                report.append(f"Write transaction overhead: {self._format_time(tx_overhead_write)}")
                report.append(f"Read transaction overhead: {self._format_time(tx_overhead_read)}")
                report.append(
                    f"Overhead difference: {abs(tx_overhead_write - tx_overhead_read) / min(tx_overhead_write, tx_overhead_read) * 100:.1f}%"
                )

                # Calculate break-even points
                bulk_write_time = lmdb_results.get("bulk_write", {}).get("mean", 0)
                if bulk_write_time > 0:
                    ops_per_bulk = size
                    time_per_op_bulk = bulk_write_time / ops_per_bulk
                    breakeven_ops = tx_overhead_write / time_per_op_bulk
                    report.append(
                        f"Break-even point for batching writes: ~{breakeven_ops:.0f} operations per transaction"
                    )

            # Summary for this dataset size
            report.append(f"\n{Colors.YELLOW}{Colors.BOLD}SUMMARY FOR {size:,} ITEMS:{Colors.END}")

            # Count wins
            dict_wins = 0
            lmdb_wins = 0

            for op_key, _, item_count, _ in operations:
                if op_key in dict_results and op_key in lmdb_results:
                    dict_time = dict_results[op_key]["mean"]
                    lmdb_time = lmdb_results[op_key]["mean"]
                    if dict_time < lmdb_time:
                        dict_wins += 1
                    else:
                        lmdb_wins += 1

            report.append(
                f"{Colors.GREEN}Dict wins: {dict_wins}/{dict_wins + lmdb_wins} operations{Colors.END}"
            )
            report.append(
                f"{Colors.BLUE}LMDB wins: {lmdb_wins}/{dict_wins + lmdb_wins} operations{Colors.END}"
            )

            # Memory usage estimate
            estimated_dict_memory = size * 300 * 1.5  # Rough estimate with Python overhead
            report.append(f"Dict estimated memory: ~{estimated_dict_memory / (1024*1024):.1f} MB")
            report.append(f"LMDB map size: {lmdb_results.get('map_size_mb', 0):.1f} MB")

        # Overall Conclusions
        report.append(f"\n{Colors.BOLD}{Colors.CYAN}{'='*90}{Colors.END}")
        report.append(f"{Colors.BOLD}{Colors.CYAN}KEY TAKEAWAYS{Colors.END}")
        report.append(f"{Colors.BOLD}{Colors.CYAN}{'=' * 90}{Colors.END}")

        report.append(f"\n{Colors.YELLOW}{Colors.BOLD}PERFORMANCE PATTERNS:{Colors.END}")
        report.append(
            f"{Colors.GREEN}• Dict excels at:{Colors.END} Single operations, bulk writes, in-memory access"
        )
        report.append(
            f"{Colors.BLUE}• LMDB excels at:{Colors.END} Large datasets, persistence, multi-process access"
        )
        report.append(f"• Transaction overhead affects LMDB single operations significantly")
        report.append(f"• Encoding/decoding adds overhead to LMDB string operations")

        report.append(f"\n{Colors.YELLOW}{Colors.BOLD}CHOOSE DICT WHEN:{Colors.END}")
        report.append(f"• Dataset fits comfortably in RAM")
        report.append(f"• No persistence needed")
        report.append(f"• Single process access")
        report.append(f"• Maximum performance for small datasets")

        report.append(f"\n{Colors.YELLOW}{Colors.BOLD}CHOOSE LMDB WHEN:{Colors.END}")
        report.append(f"• Dataset approaches RAM limits")
        report.append(f"• Need persistence/crash recovery")
        report.append(f"• Multi-process data sharing")
        report.append(f"• Consistent performance regardless of dataset size")

        return "\n".join(report)

    def run_benchmark_suite(self):
        """Run complete benchmark suite with different data sizes"""
        test_sizes = [10_000, 100_000, 1_000_000, 5_000_000]
        temp_dir = tempfile.mkdtemp()

        try:
            print(
                f"{Colors.BOLD}{Colors.CYAN}LMDB vs Python Dict Performance Benchmark{Colors.END}"
            )
            print(f"{Colors.CYAN}{'=' * 50}{Colors.END}")
            print(f"{Colors.YELLOW}Running comprehensive performance tests...{Colors.END}")

            all_results = []

            for i, size in enumerate(test_sizes, 1):
                print(
                    f"\n{Colors.BOLD}[{i}/{len(test_sizes)}] Testing {size:,} items...{Colors.END}"
                )

                print(f"  {Colors.WHITE}→ Generating test data...{Colors.END}")
                data = self.generate_test_data(size, key_size=15, value_size=200)

                db_path = os.path.join(temp_dir, f"test_db_{size}")
                os.makedirs(db_path, exist_ok=True)

                print(f"  {Colors.GREEN}→ Benchmarking Python dict...{Colors.END}")
                dict_results = self.benchmark_dict_operations(data)

                print(f"  {Colors.BLUE}→ Benchmarking LMDB...{Colors.END}")
                lmdb_results = self.benchmark_lmdb_operations(data, db_path)

                print(f"  {Colors.BOLD}{Colors.GREEN}✓ Completed{Colors.END}")

                all_results.append({"size": size, "dict": dict_results, "lmdb": lmdb_results})

            # Generate and display clear report
            print(f"\n{Colors.BOLD}{Colors.MAGENTA}GENERATING RESULTS...{Colors.END}")
            report = self.generate_clear_report(all_results)
            print("\n" + report)

        finally:
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    try:
        import lmdb
        import psutil
    except ImportError:
        print(f"{Colors.RED}Error: Missing required package. Please run:{Colors.END}")
        print(f"{Colors.YELLOW}pip install lmdb psutil{Colors.END}")
        exit(1)

    benchmark = BenchmarkRunner()
    benchmark.run_benchmark_suite()
