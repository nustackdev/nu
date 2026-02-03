"""Benchmark script for everybase flows.

Tests performance of various flow operations:
- set() commands
- get() commands
- Sequence execution
- ForRange iteration
- Parallel execution
- Conditional (If) execution
"""

import asyncio

import everybase.abc as e
from everyshape import Shape


# =============================================
# Shapes for benchmarking
# =============================================


class Metrics(Shape):
    """Metrics storage for benchmark results."""

    # Timing results (in seconds)
    set_time = e.slot.FloatSlot()
    get_time = e.slot.FloatSlot()
    sequence_time = e.slot.FloatSlot()
    forrange_time = e.slot.FloatSlot()
    parallel_time = e.slot.FloatSlot()
    if_time = e.slot.FloatSlot()
    nested_time = e.slot.FloatSlot()

    # Counters
    counter = e.slot.IntSlot()
    iterations = e.slot.IntSlot()


class BenchState(Shape):
    """State used during benchmarks."""

    value = e.slot.IntSlot()
    flag = e.slot.BoolSlot()
    nums = e.slot.ListSlot(int)


# =============================================
# Benchmark Configuration
# =============================================

N = 1000  # Number of operations per benchmark


# =============================================
# Benchmark Flows
# =============================================


# --- Benchmark: 1000 set() commands ---
bench_set = e.flow.Timed(
    e.flow.Seq(*[BenchState.value.set(i) for i in range(N)]),
    Metrics.set_time,
)


# --- Benchmark: 1000 get() commands (with set to use the value) ---
bench_get = e.flow.Timed(
    e.flow.Seq(*[BenchState.value.set(BenchState.value.get()) for _ in range(N)]),
    Metrics.get_time,
)


# --- Benchmark: Sequence with N children ---
bench_sequence = e.flow.Timed(
    e.flow.Seq(
        BenchState.value.set(0),
        *[BenchState.value.set(BenchState.value.get() + 1) for _ in range(N)],
    ),
    Metrics.sequence_time,
)


# --- Benchmark: ForRange with N iterations ---
bench_forrange = e.flow.Timed(
    e.flow.Seq(
        BenchState.value.set(0),
        e.flow.ForRange(0, N, BenchState.value.set(BenchState.value.get() + 1)),
    ),
    Metrics.forrange_time,
)


# --- Benchmark: Parallel execution (10 parallel x 100 iterations each) ---
bench_parallel = e.flow.Timed(
    e.flow.Parallel(
        *[
            e.flow.ForRange(0, N // 10, BenchState.value.set(BenchState.value.get() + 1))
            for _ in range(10)
        ]
    ),
    Metrics.parallel_time,
)


# --- Benchmark: If conditions (N iterations with condition check) ---
bench_if = e.flow.Timed(
    e.flow.Seq(
        BenchState.flag.set(True),
        BenchState.value.set(0),
        e.flow.ForRange(
            0,
            N,
            e.flow.If(
                BenchState.flag.get(),
                BenchState.value.set(BenchState.value.get() + 1),
            ),
        ),
    ),
    Metrics.if_time,
)


# --- Benchmark: Nested structures (Seq inside ForRange inside Seq) ---
bench_nested = e.flow.Timed(
    e.flow.Seq(
        BenchState.value.set(0),
        e.flow.ForRange(
            0,
            N // 10,
            e.flow.Seq(
                BenchState.value.set(BenchState.value.get() + 1),
                e.flow.ForRange(
                    0,
                    10,
                    BenchState.value.set(BenchState.value.get() + 1),
                ),
            ),
        ),
    ),
    Metrics.nested_time,
)


# =============================================
# Main benchmark flow
# =============================================


main_flow = e.flow.Seq(
    e.flow.Print("=" * 50),
    e.flow.Print(f"Everybase Flow Benchmark (N={N})"),
    e.flow.Print("=" * 50),
    e.flow.Print(""),
    # Initialize
    BenchState.value.set(0),
    BenchState.flag.set(False),
    # Run benchmarks
    e.flow.Print("Running benchmarks..."),
    e.flow.Print(""),
    # 1. Set benchmark
    e.flow.Print("[1/7] Benchmarking set() commands..."),
    bench_set,
    e.flow.Print("  set(): {:.4f}s", Metrics.set_time.get()),
    e.flow.Print(""),
    # 2. Get benchmark
    e.flow.Print("[2/7] Benchmarking get() commands..."),
    bench_get,
    e.flow.Print("  get(): {:.4f}s", Metrics.get_time.get()),
    e.flow.Print(""),
    # 3. Sequence benchmark
    e.flow.Print("[3/7] Benchmarking Sequence..."),
    bench_sequence,
    e.flow.Print("  Sequence: {:.4f}s", Metrics.sequence_time.get()),
    e.flow.Print(""),
    # 4. ForRange benchmark
    e.flow.Print("[4/7] Benchmarking ForRange..."),
    bench_forrange,
    e.flow.Print("  ForRange: {:.4f}s", Metrics.forrange_time.get()),
    e.flow.Print(""),
    # 5. Parallel benchmark
    e.flow.Print("[5/7] Benchmarking Parallel..."),
    bench_parallel,
    e.flow.Print("  Parallel: {:.4f}s", Metrics.parallel_time.get()),
    e.flow.Print(""),
    # 6. If benchmark
    e.flow.Print("[6/7] Benchmarking If conditions..."),
    bench_if,
    e.flow.Print("  If: {:.4f}s", Metrics.if_time.get()),
    e.flow.Print(""),
    # 7. Nested benchmark
    e.flow.Print("[7/7] Benchmarking nested structures..."),
    bench_nested,
    e.flow.Print("  Nested: {:.4f}s", Metrics.nested_time.get()),
    e.flow.Print(""),
    # Summary
    e.flow.Print("=" * 50),
    e.flow.Print("Benchmark complete!"),
    e.flow.Print("=" * 50),
)


# =============================================
# Execution
# =============================================


async def main():
    from everybase.abc import regular_provider, rocksdb_storage_inmemory

    with rocksdb_storage_inmemory(".db_bench_flows") as storage:
        await main_flow.start_flow(regular_provider(storage))


if __name__ == "__main__":
    asyncio.run(main())
