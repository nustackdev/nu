#!/usr/bin/env python3
"""
Execution Backend Benchmark: Multiprocessing vs Ray

Benchmarks task dispatch and execution performance for different computational loads.
"""

import math
import multiprocessing as mp
import statistics
import time
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, List


# Color codes for terminal output
class Colors:
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")


def print_section(text: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{text}{Colors.END}")
    print(f"{Colors.CYAN}{'-'*len(text)}{Colors.END}")


def print_result(label: str, value: str, color: str = Colors.WHITE):
    print(f"{Colors.BOLD}{label:<30}{Colors.END} {color}{value}{Colors.END}")


def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")


def print_success(text: str):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text: str):
    print(f"{Colors.RED}❌ {text}{Colors.END}")


# Computational tasks of varying intensity
def light_task(task_id: int) -> float:
    """Light computational task: 100 iterations"""
    result = 0.0
    for i in range(100):
        result += math.sin(i) * math.cos(i) + math.sqrt(abs(i + 1))
    return result


def medium_task(task_id: int) -> float:
    """Medium computational task: 10,000 iterations"""
    result = 0.0
    for i in range(10_000):
        result += math.sin(i) * math.cos(i) + math.sqrt(abs(i + 1))
    return result


def heavy_task(task_id: int) -> float:
    """Heavy computational task: 1,000,000 iterations"""
    result = 0.0
    for i in range(1_000_000):
        result += math.sin(i) * math.cos(i) + math.sqrt(abs(i + 1))
    return result


# Ray versions of tasks
try:
    import ray

    @ray.remote
    def ray_light_task(task_id: int) -> float:
        return light_task(task_id)

    @ray.remote
    def ray_medium_task(task_id: int) -> float:
        return medium_task(task_id)

    @ray.remote
    def ray_heavy_task(task_id: int) -> float:
        return heavy_task(task_id)

    RAY_AVAILABLE = True
except ImportError:
    print_warning("Ray not available. Install with: pip install ray")
    RAY_AVAILABLE = False


class BenchmarkStats:
    def __init__(self, times: List[float]):
        self.times = times
        self.mean = statistics.mean(times)
        self.median = statistics.median(times)
        self.stdev = statistics.stdev(times) if len(times) > 1 else 0
        self.min = min(times)
        self.max = max(times)
        self.p95 = self._percentile(times, 0.95)
        self.p99 = self._percentile(times, 0.99)

    @staticmethod
    def _percentile(data: List[float], percentile: float) -> float:
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        return sorted_data[min(index, len(sorted_data) - 1)]


def format_time(seconds: float) -> str:
    """Format time with appropriate units"""
    if seconds < 1e-6:
        return f"{seconds * 1e9:.1f}ns"
    elif seconds < 1e-3:
        return f"{seconds * 1e6:.1f}μs"
    elif seconds < 1:
        return f"{seconds * 1e3:.1f}ms"
    else:
        return f"{seconds:.3f}s"


def format_throughput(ops_per_sec: float) -> str:
    """Format throughput with appropriate units"""
    if ops_per_sec > 1000:
        return f"{ops_per_sec/1000:.1f}K ops/sec"
    else:
        return f"{ops_per_sec:.1f} ops/sec"


def print_stats(stats: BenchmarkStats, label: str):
    """Print detailed statistics"""
    print_result(f"{label} Mean:", format_time(stats.mean), Colors.GREEN)
    print_result(f"{label} Median:", format_time(stats.median), Colors.WHITE)
    print_result(f"{label} P95:", format_time(stats.p95), Colors.YELLOW)
    print_result(f"{label} P99:", format_time(stats.p99), Colors.RED)
    print_result(f"{label} Std Dev:", format_time(stats.stdev), Colors.PURPLE)
    print_result(
        f"{label} Range:", f"{format_time(stats.min)} - {format_time(stats.max)}", Colors.CYAN
    )


def benchmark_multiprocessing_latency(task_func, num_tasks: int = 100) -> Dict[str, BenchmarkStats]:
    """Benchmark multiprocessing with breakdown of dispatch vs execution vs retrieval"""
    dispatch_times = []
    total_times = []

    with ProcessPoolExecutor(max_workers=mp.cpu_count()) as executor:
        # Warm up
        list(executor.map(task_func, range(10)))

        # Benchmark with timing breakdown
        for i in range(num_tasks):
            # Measure dispatch time (submit until future is created)
            dispatch_start = time.perf_counter()
            future = executor.submit(task_func, i)
            dispatch_end = time.perf_counter()
            dispatch_times.append(dispatch_end - dispatch_start)

            # Measure total time (submit until result retrieved)
            total_start = dispatch_start
            future.result()
            total_end = time.perf_counter()
            total_times.append(total_end - total_start)

    return {"dispatch": BenchmarkStats(dispatch_times), "total": BenchmarkStats(total_times)}


def benchmark_multiprocessing_throughput(task_func, num_tasks: int = 1000) -> float:
    """Benchmark throughput with multiprocessing"""
    with ProcessPoolExecutor(max_workers=mp.cpu_count()) as executor:
        # Warm up
        list(executor.map(task_func, range(10)))

        # Benchmark throughput
        start_time = time.perf_counter()
        list(executor.map(task_func, range(num_tasks)))
        end_time = time.perf_counter()

        total_time = end_time - start_time
        return num_tasks / total_time


def benchmark_ray_latency(task_func, num_tasks: int = 100) -> Dict[str, BenchmarkStats]:
    """Benchmark Ray with breakdown of dispatch vs execution vs retrieval"""
    dispatch_times = []
    total_times = []

    # Warm up
    warmup_futures = [task_func.remote(i) for i in range(10)]
    ray.get(warmup_futures)

    # Benchmark with timing breakdown
    for i in range(num_tasks):
        # Measure dispatch time (remote call until ObjectRef created)
        dispatch_start = time.perf_counter()
        future = task_func.remote(i)
        dispatch_end = time.perf_counter()
        dispatch_times.append(dispatch_end - dispatch_start)

        # Measure total time (remote call until result retrieved)
        total_start = dispatch_start
        ray.get(future)
        total_end = time.perf_counter()
        total_times.append(total_end - total_start)

    return {"dispatch": BenchmarkStats(dispatch_times), "total": BenchmarkStats(total_times)}


def benchmark_ray_throughput(task_func, num_tasks: int = 1000) -> float:
    """Benchmark throughput with Ray"""
    # Warm up
    warmup_futures = [task_func.remote(i) for i in range(10)]
    ray.get(warmup_futures)

    # Benchmark throughput
    start_time = time.perf_counter()
    futures = [task_func.remote(i) for i in range(num_tasks)]
    ray.get(futures)
    end_time = time.perf_counter()

    total_time = end_time - start_time
    return num_tasks / total_time


def run_benchmark_suite():
    """Run the complete benchmark suite"""
    print_header("EXECUTION BACKEND BENCHMARK")
    print_result("CPU Count:", str(mp.cpu_count()), Colors.CYAN)
    print_result(
        "Ray Available:", str(RAY_AVAILABLE), Colors.GREEN if RAY_AVAILABLE else Colors.RED
    )

    if RAY_AVAILABLE:
        print_section("Initializing Ray")
        ray.init(ignore_reinit_error=True, log_to_driver=False)
        print_success("Ray initialized")

    # Task configurations
    configs = [
        (
            "Light Task (100 iterations)",
            light_task,
            ray_light_task if RAY_AVAILABLE else None,
            100,
            1000,
        ),
        (
            "Medium Task (10K iterations)",
            medium_task,
            ray_medium_task if RAY_AVAILABLE else None,
            50,
            500,
        ),
        (
            "Heavy Task (1M iterations)",
            heavy_task,
            ray_heavy_task if RAY_AVAILABLE else None,
            20,
            100,
        ),
    ]

    results = {}

    for task_name, mp_task, ray_task, latency_samples, throughput_samples in configs:
        print_section(f"Benchmarking {task_name}")

        # Multiprocessing benchmarks
        print(f"\n{Colors.BOLD}Multiprocessing Results:{Colors.END}")
        try:
            mp_latency_results = benchmark_multiprocessing_latency(mp_task, latency_samples)
            mp_throughput = benchmark_multiprocessing_throughput(mp_task, throughput_samples)

            print_stats(mp_latency_results["dispatch"], "Dispatch")
            print_stats(mp_latency_results["total"], "Total (End-to-End)")

            # Calculate execution time (total - dispatch)
            execution_times = [
                total - dispatch
                for total, dispatch in zip(
                    mp_latency_results["total"].times, mp_latency_results["dispatch"].times
                )
            ]
            execution_stats = BenchmarkStats(execution_times)
            print_stats(execution_stats, "Execution (Computed)")

            print_result("Throughput:", format_throughput(mp_throughput), Colors.GREEN)

            results[f"{task_name}_mp"] = {
                "dispatch_mean": mp_latency_results["dispatch"].mean,
                "execution_mean": execution_stats.mean,
                "total_mean": mp_latency_results["total"].mean,
                "throughput": mp_throughput,
            }
        except Exception as e:
            print_error(f"Multiprocessing benchmark failed: {e}")
            continue

        # Ray benchmarks
        if RAY_AVAILABLE and ray_task:
            print(f"\n{Colors.BOLD}Ray Results:{Colors.END}")
            try:
                ray_latency_results = benchmark_ray_latency(ray_task, latency_samples)
                ray_throughput = benchmark_ray_throughput(ray_task, throughput_samples)

                print_stats(ray_latency_results["dispatch"], "Dispatch")
                print_stats(ray_latency_results["total"], "Total (End-to-End)")

                # Calculate execution time (total - dispatch)
                execution_times = [
                    total - dispatch
                    for total, dispatch in zip(
                        ray_latency_results["total"].times, ray_latency_results["dispatch"].times
                    )
                ]
                execution_stats = BenchmarkStats(execution_times)
                print_stats(execution_stats, "Execution (Computed)")

                print_result("Throughput:", format_throughput(ray_throughput), Colors.GREEN)

                results[f"{task_name}_ray"] = {
                    "dispatch_mean": ray_latency_results["dispatch"].mean,
                    "execution_mean": execution_stats.mean,
                    "total_mean": ray_latency_results["total"].mean,
                    "throughput": ray_throughput,
                }

                # Detailed comparison
                print(f"\n{Colors.BOLD}Component Breakdown Comparison:{Colors.END}")

                mp_data = results[f"{task_name}_mp"]
                ray_data = results[f"{task_name}_ray"]

                dispatch_ratio = mp_data["dispatch_mean"] / ray_data["dispatch_mean"]
                execution_ratio = mp_data["execution_mean"] / ray_data["execution_mean"]
                total_ratio = mp_data["total_mean"] / ray_data["total_mean"]
                throughput_ratio = ray_data["throughput"] / mp_data["throughput"]

                print_result(
                    "Dispatch Overhead (MP/Ray):",
                    f"{dispatch_ratio:.2f}x",
                    Colors.GREEN if dispatch_ratio < 1 else Colors.RED,
                )
                print_result(
                    "Execution Time (MP/Ray):",
                    f"{execution_ratio:.2f}x",
                    Colors.GREEN if abs(execution_ratio - 1.0) < 0.1 else Colors.YELLOW,
                )
                print_result(
                    "Total Latency (MP/Ray):",
                    f"{total_ratio:.2f}x",
                    Colors.GREEN if total_ratio < 1 else Colors.RED,
                )
                print_result(
                    "Throughput Ratio (Ray/MP):",
                    f"{throughput_ratio:.2f}x",
                    Colors.GREEN if throughput_ratio > 1 else Colors.RED,
                )

                # Analysis
                print(f"\n{Colors.BOLD}Analysis:{Colors.END}")
                if abs(execution_ratio - 1.0) > 0.2:
                    print_warning(
                        f"Execution times differ by {abs(execution_ratio-1)*100:.1f}% - possible measurement error"
                    )
                else:
                    print_success("Execution times are similar - measurement looks valid")

                if dispatch_ratio < 0.5:
                    print_success("Multiprocessing has significantly lower dispatch overhead")
                elif dispatch_ratio < 1.0:
                    print(f"{Colors.YELLOW}Multiprocessing has lower dispatch overhead{Colors.END}")
                else:
                    print(f"{Colors.RED}Ray has lower dispatch overhead{Colors.END}")

            except Exception as e:
                print_error(f"Ray benchmark failed: {e}")

    # Summary
    print_header("BENCHMARK SUMMARY")

    if RAY_AVAILABLE:
        print_section("Performance Comparison")

        for task_name, _, _, _, _ in configs:
            mp_key = f"{task_name}_mp"
            ray_key = f"{task_name}_ray"

            if mp_key in results and ray_key in results:
                mp_data = results[mp_key]
                ray_data = results[ray_key]

                print(f"\n{Colors.BOLD}{task_name}:{Colors.END}")
                print_result("  MP Dispatch:", format_time(mp_data["dispatch_mean"]))
                print_result("  Ray Dispatch:", format_time(ray_data["dispatch_mean"]))
                print_result("  MP Execution:", format_time(mp_data["execution_mean"]))
                print_result("  Ray Execution:", format_time(ray_data["execution_mean"]))
                print_result("  MP Total:", format_time(mp_data["total_mean"]))
                print_result("  Ray Total:", format_time(ray_data["total_mean"]))
                print_result("  MP Throughput:", format_throughput(mp_data["throughput"]))
                print_result("  Ray Throughput:", format_throughput(ray_data["throughput"]))

                # Winners by category
                dispatch_winner = (
                    "MP" if mp_data["dispatch_mean"] < ray_data["dispatch_mean"] else "Ray"
                )
                total_winner = "MP" if mp_data["total_mean"] < ray_data["total_mean"] else "Ray"
                throughput_winner = (
                    "MP" if mp_data["throughput"] > ray_data["throughput"] else "Ray"
                )

                print_result("  Dispatch Winner:", dispatch_winner, Colors.GREEN)
                print_result("  Total Latency Winner:", total_winner, Colors.GREEN)
                print_result("  Throughput Winner:", throughput_winner, Colors.GREEN)

    print_section("Key Insights")
    print("• Dispatch Overhead: How long to submit a task")
    print("• Execution Time: How long the actual computation takes (should be ~identical)")
    print("• Total Latency: End-to-end time from submit to result")
    print("• If execution times differ significantly, there may be measurement issues")
    print("")
    print_section("Recommendations")
    print("• For minimal dispatch overhead: Use multiprocessing")
    print("• For distributed workloads: Use Ray despite overhead")
    print("• For light tasks: Dispatch overhead dominates, choose accordingly")
    print("• For heavy tasks: Execution time dominates, overhead becomes negligible")

    if RAY_AVAILABLE:
        ray.shutdown()


if __name__ == "__main__":
    run_benchmark_suite()
