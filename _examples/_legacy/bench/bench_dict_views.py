"""Benchmark script comparing dict view variants.

Compares performance of:
- DictView (full featured)
- FlatDictView (length tracking, primitives only)
- LightDictView (minimal, no length tracking)
"""

from __future__ import annotations

import time
from pathlib import Path


# =============================================
# Benchmark Configuration
# =============================================

N = 1000  # Number of operations per benchmark


# =============================================
# Benchmark Functions
# =============================================


def bench_set(view: object, n: int = N) -> float:
    """Benchmark N set operations."""
    start = time.perf_counter()
    for i in range(n):
        view[f"key_{i}"] = i  # type: ignore
    return time.perf_counter() - start


def bench_get(view: object, n: int = N) -> float:
    """Benchmark N get operations (assumes keys exist)."""
    start = time.perf_counter()
    for i in range(n):
        _ = view[f"key_{i}"]  # type: ignore
    return time.perf_counter() - start


def bench_contains(view: object, n: int = N) -> float:
    """Benchmark N __contains__ checks."""
    start = time.perf_counter()
    for i in range(n):
        _ = f"key_{i}" in view  # type: ignore
    return time.perf_counter() - start


def bench_iter_keys(view: object) -> float:
    """Benchmark iterating all keys."""
    start = time.perf_counter()
    for _ in view.keys():  # type: ignore
        pass
    return time.perf_counter() - start


def bench_iter_items(view: object) -> float:
    """Benchmark iterating all items."""
    start = time.perf_counter()
    for _ in view.items():  # type: ignore
        pass
    return time.perf_counter() - start


def bench_update_existing(view: object, n: int = N) -> float:
    """Benchmark N updates to existing keys."""
    start = time.perf_counter()
    for i in range(n):
        view[f"key_{i}"] = i * 2  # type: ignore
    return time.perf_counter() - start


def bench_delete(view: object, n: int = N) -> float:
    """Benchmark N delete operations."""
    start = time.perf_counter()
    for i in range(n):
        del view[f"key_{i}"]  # type: ignore
    return time.perf_counter() - start


# =============================================
# Main
# =============================================


def print_result(name: str, elapsed: float, ops: int = N) -> None:
    """Print benchmark result."""
    ops_per_sec = ops / elapsed if elapsed > 0 else float("inf")
    print(f"  {name:25s}: {elapsed:.4f}s  ({ops_per_sec:,.0f} ops/sec)")


def run_benchmarks(view: object, name: str) -> dict[str, float]:
    """Run all benchmarks for a view and return results."""
    results: dict[str, float] = {}

    # Clear first
    if hasattr(view, "clear"):
        view.clear()  # type: ignore

    print(f"\n{name}:")
    print("-" * 50)

    # Set operations (new keys)
    results["set_new"] = bench_set(view)
    print_result("set (new keys)", results["set_new"])

    # Get operations
    results["get"] = bench_get(view)
    print_result("get", results["get"])

    # Contains checks
    results["contains"] = bench_contains(view)
    print_result("__contains__", results["contains"])

    # Iteration
    results["iter_keys"] = bench_iter_keys(view)
    print_result(f"iter keys ({N})", results["iter_keys"], N)

    results["iter_items"] = bench_iter_items(view)
    print_result(f"iter items ({N})", results["iter_items"], N)

    # Update existing keys
    results["set_existing"] = bench_update_existing(view)
    print_result("set (existing keys)", results["set_existing"])

    # Delete operations
    results["delete"] = bench_delete(view)
    print_result("delete", results["delete"])

    return results


def main() -> None:
    from everybase.abc import BinaryCodec, DictView, FlatDictView, LightDictView, RocksDBStorage

    print("=" * 60)
    print(f"Dict View Benchmarks (N={N})")
    print("=" * 60)

    all_results: dict[str, dict[str, float]] = {}

    with (
        RocksDBStorage(path=Path(".db_bench_dict"), codec=BinaryCodec()) as storage,
        storage.transaction() as tx,
    ):
        # Benchmark DictView
        dict_view = DictView.open_root(tx)

        regular_dict = dict_view.open_child("reg", DictView)
        all_results["DictView"] = run_benchmarks(regular_dict, "DictView (full featured)")

        # Benchmark FlatDictView
        flat_view = dict_view.open_child("flat", FlatDictView)
        all_results["FlatDictView"] = run_benchmarks(flat_view, "FlatDictView (with len)")

        # Benchmark LightDictView
        light_view = dict_view.open_child("light", LightDictView)
        all_results["LightDictView"] = run_benchmarks(light_view, "LightDictView (minimal)")

    # Summary comparison
    print("\n" + "=" * 60)
    print("Performance Comparison (relative to DictView)")
    print("=" * 60)

    base = all_results["DictView"]
    for view_name in ["FlatDictView", "LightDictView"]:
        print(f"\n{view_name}:")
        for op, time_val in all_results[view_name].items():
            base_time = base[op]
            speedup = base_time / time_val if time_val > 0 else float("inf")
            indicator = "faster" if speedup > 1 else "slower"
            print(f"  {op:25s}: {speedup:.2f}x {indicator}")

    print("\n" + "=" * 60)
    print("Benchmark complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
