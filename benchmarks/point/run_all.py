"""Run all point benchmark scenarios and collect results into RESULTS.md."""

from __future__ import annotations

import asyncio
import importlib
import sys
import time
from datetime import datetime
from pathlib import Path


_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))  # benchmarks/ — for utils
sys.path.insert(0, str(_HERE))  # benchmarks/point/ — for scenario modules

from utils import TimingResult, format_counter_table, format_result_table  # noqa: E402


SCENARIOS = [
    ("Scenario 0: Raw TKV RocksDB", "00_raw_tkv"),
    ("Scenario 1: Flat Writes", "01_flat_writes"),
    ("Scenario 2: Nested Shape Navigation", "02_nested_nav"),
    ("Scenario 3: Dict-of-Shapes CRUD", "03_dict_shapes"),
    ("Scenario 4: List Append & Iteration", "04_list_ops"),
    ("Scenario 5: Mixed Read/Write Flow", "05_mixed_flow"),
    ("Scenario 6: Auto-Atomic Granularity", "06_atomic_granularity"),
    ("Scenario 7: Observer Overhead", "07_observer_overhead"),
]


async def main() -> None:
    all_results: dict[str, list[TimingResult]] = {}

    print("=" * 70)
    print("  EVERYBASE DATA LAYER BENCHMARKS — Point Suite")
    print("=" * 70)
    print()

    start = time.perf_counter()

    for name, module_name in SCENARIOS:
        print(f">>> Running {name}...")
        mod = importlib.import_module(module_name)
        all_results[name] = await mod.run_all()
        print()

    total_time = time.perf_counter() - start

    # Generate RESULTS.md
    lines = [
        "# Everybase Data Layer Benchmark Results — Point Suite",
        "",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"**Total runtime:** {total_time:.1f}s  ",
        f"**Python:** {sys.version.split()[0]}  ",
        "",
        "---",
        "",
    ]

    for scenario_name, results in all_results.items():
        lines.append(f"## {scenario_name}")
        lines.append("")
        lines.append("### Timing")
        lines.append("")
        lines.append(format_result_table(results))
        lines.append("")
        lines.append("### Counters")
        lines.append("")
        lines.append(format_counter_table(results))
        lines.append("")
        lines.append("---")
        lines.append("")

    # Summary
    lines.append("## Key Observations")
    lines.append("")

    # Raw TKV baseline (from scenario 0)
    s0 = all_results.get("Scenario 0: Raw TKV RocksDB", [])
    raw_5k = next((r for r in s0 if "raw_put_5keys x" in r.name and "1txn" not in r.name), None)
    raw_1txn = next((r for r in s0 if "1txn" in r.name), None)
    raw_get = next((r for r in s0 if "raw_get" in r.name), None)
    if raw_5k:
        lines.append(
            f"- **Raw TKV RocksDB (5 puts, 1 txn each):** {raw_5k.ops_per_sec:,.0f} ops/sec "
            f"({raw_5k.per_op_ms:.3f}ms/op)"
        )
    if raw_1txn:
        lines.append(
            f"- **Raw TKV RocksDB (5 puts, single txn):** {raw_1txn.ops_per_sec:,.0f} ops/sec "
            f"({raw_1txn.per_op_ms:.3f}ms/op)"
        )
    if raw_get:
        lines.append(
            f"- **Raw TKV RocksDB (5 gets):** {raw_get.ops_per_sec:,.0f} ops/sec "
            f"({raw_get.per_op_ms:.3f}ms/op)"
        )

    # auto_atomic vs single atomic comparison (from scenario 6)
    s6 = all_results.get("Scenario 6: Auto-Atomic Granularity", [])
    if len(s6) >= 3:
        auto = next((r for r in s6 if "auto_atomic_per_term" in r.name), None)
        single = next((r for r in s6 if r.name.startswith("single_atomic")), None)
        raw = next((r for r in s6 if "raw_dictview" in r.name), None)
        if auto and single and raw:
            lines.append(
                f"- **auto_atomic per-term overhead:** {auto.per_op_ms:.3f}ms/op "
                f"({auto.counters.get('storage.begin_transaction', 0)} txns/op)"
            )
            lines.append(
                f"- **Single Atomic:** {single.per_op_ms:.3f}ms/op "
                f"({single.counters.get('storage.begin_transaction', 0)} txns/op)"
            )
            lines.append(
                f"- **Raw DictView:** {raw.per_op_ms:.3f}ms/op "
                f"({raw.counters.get('storage.begin_transaction', 0)} txns/op)"
            )
            if raw.per_op_ms > 0:
                lines.append(
                    f"- **Framework overhead vs raw:** "
                    f"{auto.per_op_ms / raw.per_op_ms:.1f}x (auto_atomic), "
                    f"{single.per_op_ms / raw.per_op_ms:.1f}x (single Atomic)"
                )

    # Nesting depth impact (from scenario 2)
    s2 = all_results.get("Scenario 2: Nested Shape Navigation", [])
    d2_w = next((r for r in s2 if "depth_2_write" in r.name), None)
    d6_w = next((r for r in s2 if "depth_6_write" in r.name), None)
    if d2_w and d6_w:
        lines.append(
            f"- **Nesting depth cost:** depth-2 write = {d2_w.per_op_ms:.3f}ms, "
            f"depth-6 write = {d6_w.per_op_ms:.3f}ms "
            f"({d6_w.per_op_ms / d2_w.per_op_ms:.1f}x)"
        )

    # Observer impact (from scenario 7)
    s7 = all_results.get("Scenario 7: Observer Overhead", [])
    with_obs = next((r for r in s7 if r.name.startswith("with_observer")), None)
    without_obs = next((r for r in s7 if r.name.startswith("without_observer")), None)
    if with_obs and without_obs:
        lines.append(
            f"- **Observer overhead:** with={with_obs.per_op_ms:.3f}ms, "
            f"without={without_obs.per_op_ms:.3f}ms "
            f"(delta={with_obs.per_op_ms - without_obs.per_op_ms:.3f}ms)"
        )

    lines.append("")

    md = "\n".join(lines)

    results_path = _HERE / "RESULTS.md"
    results_path.write_text(md)

    print("=" * 70)
    print(f"  Results written to {results_path} ({total_time:.1f}s total)")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
