"""Benchmark script for Shape system operations.

Benchmarks:
1. Primitive set/get operations
2. Shape store/extract operations
3. Simple composite query (single field access)
4. Mid composite query (multiple field access with operators)
5. Complex composite query (nested collections with transformations)
"""

from __future__ import annotations

import time
from pathlib import Path
from statistics import mean, stdev
from typing import TYPE_CHECKING

import everybase.abc as e
from everybase.abc import BinaryCodec, Context, DictView, RocksDBStorage, Shape


if TYPE_CHECKING:
    from collections.abc import Callable


# =============================================================================
# Shape Definitions
# =============================================================================


class SymbolInfo(Shape):
    """Individual symbol information."""

    price = e.s.FloatSlot()
    volume = e.s.IntSlot()
    exchange = e.s.StrSlot()
    timestamp = e.s.IntSlot()


class Order(Shape):
    """Order information."""

    id = e.s.StrSlot()
    symbol = e.s.StrSlot()
    quantity = e.s.IntSlot()
    price = e.s.FloatSlot()


class Market(Shape):
    """Market data with collections."""

    counter = e.s.IntSlot()
    signals = e.s.DictSlot(float)
    prices = e.s.ListSlot(float)
    symbols = e.s.ShapesDictSlot(SymbolInfo)
    orders = e.s.ShapesListSlot(Order)


# =============================================================================
# Benchmark Infrastructure
# =============================================================================


class Benchmark:
    """Benchmark runner with timing and statistics."""

    def __init__(self, name: str, iterations: int = 100):
        self.name = name
        self.iterations = iterations
        self.times: list[float] = []

    def run(self, func: Callable[[Context], None], ctx: Context) -> None:
        """Run benchmark iterations and collect timing data."""
        # Warmup
        for _ in range(min(10, self.iterations // 10)):
            func(ctx)

        # Actual benchmark
        self.times = []
        for _ in range(self.iterations):
            start = time.perf_counter()
            func(ctx)
            end = time.perf_counter()
            self.times.append((end - start) * 1000)  # Convert to ms

    def report(self) -> None:
        """Print benchmark results."""
        avg = mean(self.times)
        std = stdev(self.times) if len(self.times) > 1 else 0
        min_time = min(self.times)
        max_time = max(self.times)

        print(f"\n{self.name}")
        print(f"  Iterations: {self.iterations}")
        print(f"  Average:    {avg:.4f} ms")
        print(f"  Std Dev:    {std:.4f} ms")
        print(f"  Min:        {min_time:.4f} ms")
        print(f"  Max:        {max_time:.4f} ms")
        print(f"  Total:      {sum(self.times):.2f} ms")


# =============================================================================
# Benchmark Functions
# =============================================================================


def bench_primitive_set(ctx: Context) -> None:
    """Benchmark: primitive set operation."""
    Market.counter.set(42).execute(ctx)


def bench_primitive_get(ctx: Context) -> None:
    """Benchmark: primitive get operation."""
    Market.counter.get().execute(ctx)


def bench_primitive_set_get(ctx: Context) -> None:
    """Benchmark: primitive set followed by get."""
    Market.counter.set(42).execute(ctx)
    Market.counter.get().execute(ctx)


def bench_shape_store(ctx: Context) -> None:
    """Benchmark: shape store operation."""
    Market.symbols["BENCH"].store(
        {
            "price": 150.0,
            "volume": 1000000,
            "exchange": "NASDAQ",
            "timestamp": 1234567890,
        }
    ).execute(ctx)


def bench_shape_extract(ctx: Context) -> None:
    """Benchmark: shape extract operation."""
    Market.symbols["BENCH"].extract().execute(ctx)


def bench_shape_store_extract(ctx: Context) -> None:
    """Benchmark: shape store followed by extract."""
    Market.symbols["BENCH"].store(
        {
            "price": 150.0,
            "volume": 1000000,
            "exchange": "NASDAQ",
            "timestamp": 1234567890,
        }
    ).execute(ctx)
    Market.symbols["BENCH"].extract().execute(ctx)


def bench_simple_composite(ctx: Context) -> None:
    """Benchmark: simple composite query - single field access with operator."""
    (Market.symbols["BENCH"].price.get() > 100).execute(ctx)


def bench_mid_composite(ctx: Context) -> None:
    """Benchmark: mid composite query - multiple fields with chained operators."""
    ((Market.symbols["BENCH"].volume.get() >> 10) + Market.counter.get()).execute(ctx)


def bench_complex_composite(ctx: Context) -> None:
    """Benchmark: complex composite query - nested collections with transformations."""
    Market.prices[Market.counter.get()].get().execute(ctx)
    (Market.orders[0].quantity.get() * Market.symbols["BENCH"].price.get()).execute(ctx)


# =============================================================================
# Main Benchmark Runner
# =============================================================================


def setup_data(ctx: Context) -> None:
    """Setup initial data for benchmarks."""
    Market.counter.set(1).execute(ctx)

    Market.signals["vix"].set(23.5).execute(ctx)
    Market.signals["sentiment"].set(0.75).execute(ctx)

    Market.prices.append(100.5).execute(ctx)
    Market.prices.append(101.2).execute(ctx)
    Market.prices.append(99.8).execute(ctx)

    Market.symbols["BENCH"].store(
        {
            "price": 150.0,
            "volume": 1000000,
            "exchange": "NASDAQ",
            "timestamp": 1234567890,
        }
    ).execute(ctx)

    Market.orders.append(
        {
            "id": "ORD001",
            "symbol": "BENCH",
            "quantity": 100,
            "price": 150.0,
        }
    ).execute(ctx)


def run_benchmarks(ctx: Context, iterations: int = 100) -> None:
    """Run all benchmarks."""
    print("=" * 70)
    print("SHAPE SYSTEM BENCHMARKS")
    print("=" * 70)

    benchmarks = [
        ("Primitive Set", bench_primitive_set),
        ("Primitive Get", bench_primitive_get),
        ("Primitive Set+Get", bench_primitive_set_get),
        ("Shape Store", bench_shape_store),
        ("Shape Extract", bench_shape_extract),
        ("Shape Store+Extract", bench_shape_store_extract),
        ("Simple Composite (field + operator)", bench_simple_composite),
        ("Mid Composite (multi-field + chain)", bench_mid_composite),
        ("Complex Composite (nested + transform)", bench_complex_composite),
    ]

    for name, func in benchmarks:
        bench = Benchmark(name, iterations)
        bench.run(func, ctx)
        bench.report()

    print("\n" + "=" * 70)
    print("BENCHMARK COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    # Setup storage
    db_path = Path(".db_benchmark")
    iterations = 10000

    print(f"Database path: {db_path}")
    print(f"Iterations per benchmark: {iterations}\n")

    with (
        RocksDBStorage(path=Path(".db_bench_term_b"), codec=BinaryCodec()) as storage,
        storage.transaction() as tx,
    ):
        root = DictView.open_root(tx)
        ctx = Context.create(root_view=root, storage_context=tx)

        # Setup initial data
        setup_data(ctx)

        # Run benchmarks
        run_benchmarks(ctx, iterations=iterations)
