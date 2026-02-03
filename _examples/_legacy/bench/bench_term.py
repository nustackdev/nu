"""Benchmark script for everybase terms (direct execution).

Tests performance of term operations:
- set() on primitives (int, float, str)
- get() on primitives
- Dict operations (set by key, get by key)
- List operations (append, get by index)
"""

from __future__ import annotations

import time
from pathlib import Path

import everybase.abc as e
from everyshape import Context, Shape


# =============================================
# Shapes for benchmarking
# =============================================


class BenchShape(Shape):
    """Shape for benchmarking primitive operations."""

    int_val = e.slot.IntSlot()
    float_val = e.slot.FloatSlot()
    str_val = e.slot.StrSlot()
    bool_val = e.slot.BoolSlot()


class BenchCollections(Shape):
    """Shape for benchmarking collection operations."""

    int_dict = e.slot.DictSlot(int)  # e.view.LightDictView)
    float_list = e.slot.ListSlot(float)


# =============================================
# Benchmark Configuration
# =============================================

N = 1000  # Number of operations per benchmark


# =============================================
# Benchmark Functions
# =============================================


def bench_int_set(ctx: Context) -> float:
    """Benchmark N int set() operations."""
    start = time.perf_counter()
    for i in range(N):
        BenchShape.int_val.set(i).execute(ctx)
    return time.perf_counter() - start


def bench_int_get(ctx: Context) -> float:
    """Benchmark N int get() operations."""
    BenchShape.int_val.set(42).execute(ctx)
    start = time.perf_counter()
    for _ in range(N):
        BenchShape.int_val.get().execute(ctx)
    return time.perf_counter() - start


def bench_float_set(ctx: Context) -> float:
    """Benchmark N float set() operations."""
    start = time.perf_counter()
    for i in range(N):
        BenchShape.float_val.set(float(i) * 1.5).execute(ctx)
    return time.perf_counter() - start


def bench_float_get(ctx: Context) -> float:
    """Benchmark N float get() operations."""
    BenchShape.float_val.set(3.14159).execute(ctx)
    start = time.perf_counter()
    for _ in range(N):
        BenchShape.float_val.get().execute(ctx)
    return time.perf_counter() - start


def bench_str_set(ctx: Context) -> float:
    """Benchmark N str set() operations."""
    start = time.perf_counter()
    for i in range(N):
        BenchShape.str_val.set(f"value_{i}").execute(ctx)
    return time.perf_counter() - start


def bench_str_get(ctx: Context) -> float:
    """Benchmark N str get() operations."""
    BenchShape.str_val.set("benchmark_string").execute(ctx)
    start = time.perf_counter()
    for _ in range(N):
        BenchShape.str_val.get().execute(ctx)
    return time.perf_counter() - start


def bench_dict_set(ctx: Context) -> float:
    """Benchmark N dict set by key operations."""
    start = time.perf_counter()
    for i in range(N):
        BenchCollections.int_dict[f"key_{i}"].set(i).execute(ctx)
    return time.perf_counter() - start


def bench_dict_get(ctx: Context) -> float:
    """Benchmark N dict get by key operations."""
    # Setup keys first
    for i in range(N):
        BenchCollections.int_dict[f"key_{i}"].set(i).execute(ctx)
    start = time.perf_counter()
    for i in range(N):
        BenchCollections.int_dict[f"key_{i}"].get().execute(ctx)
    return time.perf_counter() - start


def bench_list_append(ctx: Context) -> float:
    """Benchmark N list append operations."""
    BenchCollections.float_list.clear().execute(ctx)
    start = time.perf_counter()
    for i in range(N):
        BenchCollections.float_list.append(float(i)).execute(ctx)
    return time.perf_counter() - start


def bench_list_get(ctx: Context) -> float:
    """Benchmark N list get by index operations."""
    # Setup list first
    BenchCollections.float_list.clear().execute(ctx)
    for i in range(N):
        BenchCollections.float_list.append(float(i)).execute(ctx)
    start = time.perf_counter()
    for i in range(N):
        BenchCollections.float_list[i].get().execute(ctx)
    return time.perf_counter() - start


def bench_computed_expr(ctx: Context) -> float:
    """Benchmark N computed expression evaluations (get + arithmetic)."""
    BenchShape.int_val.set(100).execute(ctx)
    start = time.perf_counter()
    for _ in range(N):
        (BenchShape.int_val.get() + 10).execute(ctx)
    return time.perf_counter() - start


def bench_chained_expr(ctx: Context) -> float:
    """Benchmark N chained expression evaluations."""
    BenchShape.int_val.set(100).execute(ctx)
    start = time.perf_counter()
    for _ in range(N):
        ((BenchShape.int_val.get() + 10) * 2 - 5).execute(ctx)
    return time.perf_counter() - start


# =============================================
# Main
# =============================================


def print_result(name: str, elapsed: float, ops: int = N) -> None:
    """Print benchmark result."""
    ops_per_sec = ops / elapsed if elapsed > 0 else float("inf")
    print(f"  {name:20s}: {elapsed:.4f}s  ({ops_per_sec:,.0f} ops/sec)")


def main() -> None:
    from everybase.abc import BinaryCodec, RocksDBStorage

    print("=" * 60)
    print(f"Everybase Term Benchmark (N={N})")
    print("=" * 60)
    print()

    with (
        RocksDBStorage(path=Path(".db_bench_term_b"), codec=BinaryCodec()) as storage,
        storage.transaction() as tx,
    ):
        root = e.view.DictView.open_root(tx)
        ctx = Context.create(root_view=root, storage_context=tx)

        print("Primitive set() operations:")
        print_result("int.set()", bench_int_set(ctx))
        print_result("float.set()", bench_float_set(ctx))
        print_result("str.set()", bench_str_set(ctx))
        print()

        print("Primitive get() operations:")
        print_result("int.get()", bench_int_get(ctx))
        print_result("float.get()", bench_float_get(ctx))
        print_result("str.get()", bench_str_get(ctx))
        print()

        print("Dict operations:")
        print_result("dict[key].set()", bench_dict_set(ctx))
        print_result("dict[key].get()", bench_dict_get(ctx))
        print()

        print("List operations:")
        print_result("list.append()", bench_list_append(ctx))
        print_result("list[i].get()", bench_list_get(ctx))
        print()

        print("Computed expressions:")
        print_result("get() + 10", bench_computed_expr(ctx))
        print_result("(get()+10)*2-5", bench_chained_expr(ctx))
        print()

    print("=" * 60)
    print("Benchmark complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
