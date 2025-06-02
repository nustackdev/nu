#!/usr/bin/env python3
"""
Ray vs Multiprocessing Communication Benchmark

Focuses on sequential get/set operations with 200-char strings.
Tests Ray actor coordination pattern vs multiprocessing.Queue.

Requirements: pip install ray psutil
"""

import multiprocessing
import os
import platform
import queue
import random
import statistics
import string
import sys
import time
from typing import Any, Dict, List, Tuple

try:
    import psutil
    import ray

    RAY_AVAILABLE = True
except ImportError:
    RAY_AVAILABLE = False


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
    END = "\033[0m"


class StateCoordinator:
    """Simple in-memory state coordinator for Ray actors"""

    def __init__(self):
        self.state = {}

    def get(self, key: str) -> str:
        return self.state.get(key)

    def set(self, key: str, value: str) -> bool:
        self.state[key] = value
        return True

    def batch_get(self, keys: List[str]) -> List[str]:
        return [self.state.get(key) for key in keys]

    def batch_set(self, items: List[Tuple[str, str]]) -> bool:
        for key, value in items:
            self.state[key] = value
        return True


@ray.remote
class RayStateCoordinator:
    """Ray actor version of state coordinator"""

    def __init__(self):
        self.state = {}

    def get(self, key: str) -> str:
        return self.state.get(key)

    def set(self, key: str, value: str) -> bool:
        self.state[key] = value
        return True

    def batch_get(self, keys: List[str]) -> List[str]:
        return [self.state.get(key) for key in keys]

    def batch_set(self, items: List[Tuple[str, str]]) -> bool:
        for key, value in items:
            self.state[key] = value
        return True

    def get_stats(self) -> Dict:
        return {"num_keys": len(self.state)}


@ray.remote
class RayWorker:
    """Ray worker that performs get/set operations"""

    def __init__(self, coordinator_ref):
        self.coordinator = coordinator_ref

    def sequential_ops(self, operations: List[Tuple[str, str, str]]) -> Dict[str, float]:
        """Perform sequential get/set operations
        operations: List of (op_type, key, value) tuples
        """
        times = []

        for op_type, key, value in operations:
            start_time = time.perf_counter()

            if op_type == "set":
                ray.get(self.coordinator.set.remote(key, value))
            elif op_type == "get":
                ray.get(self.coordinator.get.remote(key))

            end_time = time.perf_counter()
            times.append(end_time - start_time)

        return {
            "total_time": sum(times),
            "mean_time": statistics.mean(times),
            "individual_times": times,
        }

    def batch_ops(
        self, batch_sets: List[List[Tuple[str, str]]], batch_gets: List[List[str]]
    ) -> Dict[str, float]:
        """Perform batch operations"""
        set_times = []
        get_times = []

        # Batch sets
        for batch in batch_sets:
            start_time = time.perf_counter()
            ray.get(self.coordinator.batch_set.remote(batch))
            end_time = time.perf_counter()
            set_times.append(end_time - start_time)

        # Batch gets
        for batch in batch_gets:
            start_time = time.perf_counter()
            ray.get(self.coordinator.batch_get.remote(batch))
            end_time = time.perf_counter()
            get_times.append(end_time - start_time)

        return {
            "set_times": set_times,
            "get_times": get_times,
            "total_set_time": sum(set_times),
            "total_get_time": sum(get_times),
        }


class MultiprocessingBenchmark:
    """Benchmark using multiprocessing.Queue"""

    def __init__(self, num_workers: int = 4):
        self.num_workers = num_workers
        self.request_queue = multiprocessing.Queue()
        self.response_queue = multiprocessing.Queue()
        self.coordinator_process = None
        self.state = {}

    def coordinator_worker(self):
        """Coordinator process that manages state"""
        while True:
            try:
                request = self.request_queue.get(timeout=1)
                if request is None:  # Shutdown signal
                    break

                request_id, op_type, key, value = request

                if op_type == "set":
                    self.state[key] = value
                    self.response_queue.put((request_id, True))
                elif op_type == "get":
                    result = self.state.get(key)
                    self.response_queue.put((request_id, result))
                elif op_type == "batch_set":
                    for k, v in value:  # value contains the batch items
                        self.state[k] = v
                    self.response_queue.put((request_id, True))
                elif op_type == "batch_get":
                    results = [self.state.get(k) for k in value]  # value contains keys
                    self.response_queue.put((request_id, results))

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Coordinator error: {e}")
                break

    def start(self):
        """Start the coordinator process"""
        self.coordinator_process = multiprocessing.Process(target=self.coordinator_worker)
        self.coordinator_process.start()

    def stop(self):
        """Stop the coordinator process"""
        if self.coordinator_process:
            self.request_queue.put(None)  # Shutdown signal
            self.coordinator_process.join(timeout=5)
            if self.coordinator_process.is_alive():
                self.coordinator_process.terminate()

    def sequential_ops(self, operations: List[Tuple[str, str, str]]) -> Dict[str, float]:
        """Perform sequential operations"""
        times = []
        request_id = 0

        for op_type, key, value in operations:
            request_id += 1

            start_time = time.perf_counter()
            self.request_queue.put((request_id, op_type, key, value))

            # Wait for response
            while True:
                resp_id, result = self.response_queue.get()
                if resp_id == request_id:
                    break
                # If we get a different response, put it back (shouldn't happen in sequential)

            end_time = time.perf_counter()
            times.append(end_time - start_time)

        return {
            "total_time": sum(times),
            "mean_time": statistics.mean(times),
            "individual_times": times,
        }

    def batch_ops(
        self, batch_sets: List[List[Tuple[str, str]]], batch_gets: List[List[str]]
    ) -> Dict[str, float]:
        """Perform batch operations"""
        set_times = []
        get_times = []
        request_id = 0

        # Batch sets
        for batch in batch_sets:
            request_id += 1
            start_time = time.perf_counter()
            self.request_queue.put((request_id, "batch_set", None, batch))

            # Wait for response
            while True:
                resp_id, result = self.response_queue.get()
                if resp_id == request_id:
                    break

            end_time = time.perf_counter()
            set_times.append(end_time - start_time)

        # Batch gets
        for batch in batch_gets:
            request_id += 1
            start_time = time.perf_counter()
            self.request_queue.put((request_id, "batch_get", None, batch))

            # Wait for response
            while True:
                resp_id, result = self.response_queue.get()
                if resp_id == request_id:
                    break

            end_time = time.perf_counter()
            get_times.append(end_time - start_time)

        return {
            "set_times": set_times,
            "get_times": get_times,
            "total_set_time": sum(set_times),
            "total_get_time": sum(get_times),
        }


class BenchmarkRunner:
    def __init__(self):
        self.system_info = self._get_system_info()

    def _get_system_info(self) -> Dict:
        """Collect system information"""
        try:
            info = {
                "python_version": sys.version.split()[0],
                "platform": platform.system(),
                "cpu_count": os.cpu_count(),
                "memory_gb": round(psutil.virtual_memory().total / (1024**3), 1),
                "ray_available": RAY_AVAILABLE,
            }
            if RAY_AVAILABLE:
                info["ray_version"] = ray.__version__
            return info
        except Exception as e:
            return {"error": f"Could not collect system info: {e}"}

    def generate_test_data(
        self, num_operations: int
    ) -> Tuple[List[str], List[Tuple[str, str, str]]]:
        """Generate test data: 200-char strings"""
        random.seed(42)  # Reproducible results

        # Generate keys and values
        keys = [f"key_{i:06d}" for i in range(num_operations)]
        values = []

        for _ in range(num_operations):
            value = "".join(random.choices(string.ascii_letters + string.digits, k=200))
            values.append(value)

        # Create operations: alternating sets and gets
        operations = []
        for i in range(num_operations):
            if i % 2 == 0:  # Set operation
                operations.append(("set", keys[i], values[i]))
            else:  # Get operation (get previously set key)
                get_key = keys[i // 2] if i // 2 < len(keys) else keys[0]
                operations.append(("get", get_key, None))

        return keys, operations

    def _format_time(self, seconds: float) -> str:
        """Format time with appropriate units"""
        if seconds < 1e-6:
            return f"{seconds * 1e9:.1f}ns"
        elif seconds < 1e-3:
            return f"{seconds * 1e6:.1f}μs"
        elif seconds < 1:
            return f"{seconds * 1e3:.1f}ms"
        else:
            return f"{seconds:.2f}s"

    def _format_ops_per_second(self, seconds: float, ops: int) -> str:
        """Format operations per second"""
        if seconds <= 0:
            return "∞"
        ops_per_sec = ops / seconds
        if ops_per_sec >= 1e6:
            return f"{ops_per_sec / 1e6:.2f}M"
        elif ops_per_sec >= 1e3:
            return f"{ops_per_sec / 1e3:.1f}K"
        else:
            return f"{ops_per_sec:.0f}"

    def benchmark_ray(
        self, operations: List[Tuple[str, str, str]], num_workers: int = 4
    ) -> Dict[str, Any]:
        """Benchmark Ray communication"""
        if not RAY_AVAILABLE:
            return {"error": "Ray not available"}

        try:
            # Initialize Ray
            if not ray.is_initialized():
                ray.init(num_cpus=num_workers + 1, ignore_reinit_error=True)

            # Create coordinator and workers
            coordinator = RayStateCoordinator.remote()
            workers = [RayWorker.remote(coordinator) for _ in range(num_workers)]

            # Warmup
            warmup_ops = operations[: min(10, len(operations))]
            ray.get(workers[0].sequential_ops.remote(warmup_ops))

            # Sequential operations benchmark
            start_time = time.perf_counter()
            result = ray.get(workers[0].sequential_ops.remote(operations))
            end_time = time.perf_counter()

            result["wall_clock_time"] = end_time - start_time
            result["ops_per_second"] = len(operations) / result["wall_clock_time"]

            # Batch operations test
            batch_size = 50
            batch_sets = []
            batch_gets = []

            set_items = [(op[1], op[2]) for op in operations if op[0] == "set"]
            get_keys = [op[1] for op in operations if op[0] == "get"]

            # Create batches
            for i in range(0, len(set_items), batch_size):
                batch_sets.append(set_items[i : i + batch_size])

            for i in range(0, len(get_keys), batch_size):
                batch_gets.append(get_keys[i : i + batch_size])

            batch_result = ray.get(workers[0].batch_ops.remote(batch_sets, batch_gets))
            result["batch_results"] = batch_result

            return result

        except Exception as e:
            return {"error": f"Ray benchmark failed: {e}"}
        finally:
            if ray.is_initialized():
                ray.shutdown()

    def benchmark_multiprocessing(
        self, operations: List[Tuple[str, str, str]], num_workers: int = 4
    ) -> Dict[str, Any]:
        """Benchmark multiprocessing.Queue communication"""
        try:
            mp_benchmark = MultiprocessingBenchmark(num_workers)
            mp_benchmark.start()

            # Warmup
            warmup_ops = operations[: min(10, len(operations))]
            mp_benchmark.sequential_ops(warmup_ops)

            # Sequential operations benchmark
            start_time = time.perf_counter()
            result = mp_benchmark.sequential_ops(operations)
            end_time = time.perf_counter()

            result["wall_clock_time"] = end_time - start_time
            result["ops_per_second"] = len(operations) / result["wall_clock_time"]

            # Batch operations test
            batch_size = 50
            batch_sets = []
            batch_gets = []

            set_items = [(op[1], op[2]) for op in operations if op[0] == "set"]
            get_keys = [op[1] for op in operations if op[0] == "get"]

            # Create batches
            for i in range(0, len(set_items), batch_size):
                batch_sets.append(set_items[i : i + batch_size])

            for i in range(0, len(get_keys), batch_size):
                batch_gets.append(get_keys[i : i + batch_size])

            batch_result = mp_benchmark.batch_ops(batch_sets, batch_gets)
            result["batch_results"] = batch_result

            return result

        except Exception as e:
            return {"error": f"Multiprocessing benchmark failed: {e}"}
        finally:
            mp_benchmark.stop()

    def generate_report(self, ray_results: Dict, mp_results: Dict, num_operations: int) -> str:
        """Generate comparison report"""
        report = []

        # Header
        report.append(f"{Colors.BOLD}{Colors.CYAN}{'=' * 80}{Colors.END}")
        report.append(
            f"{Colors.BOLD}{Colors.CYAN}RAY vs MULTIPROCESSING COMMUNICATION BENCHMARK{Colors.END}"
        )
        report.append(f"{Colors.BOLD}{Colors.CYAN}{'=' * 80}{Colors.END}")

        # System info
        report.append(f"\n{Colors.YELLOW}{Colors.BOLD}SYSTEM INFO:{Colors.END}")
        info = self.system_info
        report.append(
            f"Python {info.get('python_version', 'Unknown')} | "
            f"{info.get('cpu_count', 'Unknown')} CPUs | "
            f"{info.get('memory_gb', 'Unknown')}GB RAM"
        )

        if info.get("ray_available"):
            report.append(f"Ray Version: {info.get('ray_version', 'Unknown')}")

        # Test configuration
        report.append(f"\n{Colors.YELLOW}{Colors.BOLD}TEST CONFIGURATION:{Colors.END}")
        report.append(f"• Operations: {num_operations:,} (sequential get/set)")
        report.append(f"• Data size: 200-character strings")
        report.append(f"• Pattern: Alternating set/get operations")
        report.append(f"• Workers: 4 processes")

        # Results comparison
        report.append(f"\n{Colors.BOLD}{Colors.WHITE}PERFORMANCE RESULTS:{Colors.END}")
        report.append(f"{Colors.WHITE}{'-' * 90}{Colors.END}")

        header = f"{'Metric':<25} {'Ray':<20} {'Multiprocessing':<20} {'Winner':<25}"
        report.append(f"{Colors.BOLD}{header}{Colors.END}")
        report.append(f"{Colors.WHITE}{'-' * 90}{Colors.END}")

        # Helper function to compare and format results
        def compare_metric(
            metric_name: str, ray_val: float, mp_val: float, lower_is_better: bool = True
        ):
            ray_str = (
                self._format_time(ray_val) if metric_name.endswith("Time") else f"{ray_val:.1f}"
            )
            mp_str = self._format_time(mp_val) if metric_name.endswith("Time") else f"{mp_val:.1f}"

            if lower_is_better:
                if ray_val < mp_val:
                    winner = f"{Colors.GREEN}Ray ({mp_val/ray_val:.1f}x faster){Colors.END}"
                else:
                    winner = f"{Colors.BLUE}MP ({ray_val/mp_val:.1f}x faster){Colors.END}"
            else:  # Higher is better
                if ray_val > mp_val:
                    winner = f"{Colors.GREEN}Ray ({ray_val/mp_val:.1f}x faster){Colors.END}"
                else:
                    winner = f"{Colors.BLUE}MP ({mp_val/ray_val:.1f}x faster){Colors.END}"

            return f"{metric_name:<25} {ray_str:<20} {mp_str:<20} {winner:<40}"

        if "error" not in ray_results and "error" not in mp_results:
            # Sequential operations
            report.append(
                compare_metric(
                    "Mean Op Time", ray_results["mean_time"], mp_results["mean_time"], True
                )
            )
            report.append(
                compare_metric(
                    "Total Time", ray_results["total_time"], mp_results["total_time"], True
                )
            )
            report.append(
                compare_metric(
                    "Ops/Second", ray_results["ops_per_second"], mp_results["ops_per_second"], False
                )
            )

            # Batch operations if available
            if "batch_results" in ray_results and "batch_results" in mp_results:
                ray_batch = ray_results["batch_results"]
                mp_batch = mp_results["batch_results"]

                if ray_batch.get("total_set_time") and mp_batch.get("total_set_time"):
                    report.append(
                        compare_metric(
                            "Batch Set Time",
                            ray_batch["total_set_time"],
                            mp_batch["total_set_time"],
                            True,
                        )
                    )

                if ray_batch.get("total_get_time") and mp_batch.get("total_get_time"):
                    report.append(
                        compare_metric(
                            "Batch Get Time",
                            ray_batch["total_get_time"],
                            mp_batch["total_get_time"],
                            True,
                        )
                    )

        # Error handling
        if "error" in ray_results:
            report.append(f"{Colors.RED}Ray Error: {ray_results['error']}{Colors.END}")

        if "error" in mp_results:
            report.append(f"{Colors.RED}Multiprocessing Error: {mp_results['error']}{Colors.END}")

        # Latency distribution analysis
        if (
            "error" not in ray_results
            and "error" not in mp_results
            and "individual_times" in ray_results
            and "individual_times" in mp_results
        ):

            report.append(f"\n{Colors.YELLOW}{Colors.BOLD}LATENCY DISTRIBUTION:{Colors.END}")

            ray_times = ray_results["individual_times"]
            mp_times = mp_results["individual_times"]

            ray_percentiles = (
                [statistics.quantiles(ray_times, n=100)[i - 1] for i in [50, 95, 99]]
                if len(ray_times) > 10
                else [0, 0, 0]
            )
            mp_percentiles = (
                [statistics.quantiles(mp_times, n=100)[i - 1] for i in [50, 95, 99]]
                if len(mp_times) > 10
                else [0, 0, 0]
            )

            for i, percentile in enumerate([50, 95, 99]):
                report.append(
                    compare_metric(
                        f"P{percentile} Latency", ray_percentiles[i], mp_percentiles[i], True
                    )
                )

        # Conclusions
        report.append(f"\n{Colors.BOLD}{Colors.CYAN}KEY FINDINGS:{Colors.END}")

        if "error" not in ray_results and "error" not in mp_results:
            mp_faster = mp_results["mean_time"] < ray_results["mean_time"]
            speedup = (
                ray_results["mean_time"] / mp_results["mean_time"]
                if mp_faster
                else mp_results["mean_time"] / ray_results["mean_time"]
            )

            if mp_faster:
                report.append(
                    f"{Colors.GREEN}• Multiprocessing.Queue is {speedup:.1f}x faster for sequential ops{Colors.END}"
                )
                report.append(
                    f"{Colors.BLUE}• Ray adds ~{(ray_results['mean_time'] - mp_results['mean_time']) * 1000:.1f}ms overhead per operation{Colors.END}"
                )
            else:
                report.append(
                    f"{Colors.GREEN}• Ray is {speedup:.1f}x faster for sequential ops{Colors.END}"
                )

        return "\n".join(report)

    def run_benchmark_suite(self):
        """Run the complete benchmark suite"""
        test_sizes = [20000]  # Start with smaller sizes for initial testing

        print(
            f"{Colors.BOLD}{Colors.CYAN}Ray vs Multiprocessing Communication Benchmark{Colors.END}"
        )
        print(f"{Colors.CYAN}{'=' * 55}{Colors.END}")
        print(
            f"{Colors.YELLOW}Testing sequential get/set operations with 200-char strings{Colors.END}"
        )

        for i, size in enumerate(test_sizes, 1):
            print(
                f"\n{Colors.BOLD}[{i}/{len(test_sizes)}] Testing {size:,} operations...{Colors.END}"
            )

            # Generate test data
            print(f"  {Colors.WHITE}→ Generating test data...{Colors.END}")
            keys, operations = self.generate_test_data(size)

            # Run benchmarks
            print(f"  {Colors.GREEN}→ Benchmarking Ray...{Colors.END}")
            ray_results = self.benchmark_ray(operations)

            print(f"  {Colors.BLUE}→ Benchmarking Multiprocessing...{Colors.END}")
            mp_results = self.benchmark_multiprocessing(operations)

            # Generate report
            print(f"  {Colors.BOLD}{Colors.GREEN}✓ Completed{Colors.END}")
            report = self.generate_report(ray_results, mp_results, size)
            print("\n" + report)


if __name__ == "__main__":
    if not RAY_AVAILABLE:
        print(f"{Colors.RED}Error: Ray not available. Please run:{Colors.END}")
        print(f"{Colors.YELLOW}pip install ray psutil{Colors.END}")
        exit(1)

    try:
        # Set multiprocessing start method to avoid issues on macOS
        multiprocessing.set_start_method("spawn", force=True)
    except RuntimeError:
        pass  # Already set

    benchmark = BenchmarkRunner()
    benchmark.run_benchmark_suite()
