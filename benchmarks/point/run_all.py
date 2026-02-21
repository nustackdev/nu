"""Run all point benchmark scenarios and collect results into RESULTS.md."""

from __future__ import annotations

import asyncio
import importlib
import sys
import time
from datetime import datetime
from pathlib import Path


_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))  # benchmarks/ -- for utils
sys.path.insert(0, str(_HERE))  # benchmarks/point/ -- for scenario modules

from utils import TimingResult, format_counter_table, format_result_table  # noqa: E402


SCENARIOS = [
    ("Flat Writes", "00_flat_writes"),
    ("Nested Shape Navigation", "01_nested_nav"),
    ("Dict-of-Shapes CRUD", "02_dict_shapes"),
    ("List Ops", "03_list_ops"),
    ("Atomic Granularity", "04_atomic_granularity"),
]


async def main() -> None:
    all_results: dict[str, list[TimingResult]] = {}

    print("=" * 70)
    print("  EVERYBASE POINT BENCHMARKS")
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
        "# Everybase Point Benchmark Results",
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

    # auto_atomic vs single atomic comparison
    s_atomic = all_results.get("Atomic Granularity", [])
    if len(s_atomic) >= 2:
        auto = next((r for r in s_atomic if "auto_atomic_per_term" in r.name), None)
        single = next((r for r in s_atomic if r.name.startswith("single_atomic")), None)
        if auto and single:
            lines.append(
                f"- **auto_atomic per-term:** {auto.per_op_ms:.3f}ms/op "
                f"({auto.counters.get('storage.begin_transaction', 0)} txns)"
            )
            lines.append(
                f"- **Single Atomic:** {single.per_op_ms:.3f}ms/op "
                f"({single.counters.get('storage.begin_transaction', 0)} txns)"
            )

    # Nesting depth impact
    s_nav = all_results.get("Nested Shape Navigation", [])
    d2_w = next((r for r in s_nav if "depth_2_write" in r.name), None)
    d6_w = next((r for r in s_nav if "depth_6_write" in r.name), None)
    if d2_w and d6_w:
        lines.append(
            f"- **Nesting depth cost:** depth-2 write = {d2_w.per_op_ms:.3f}ms, "
            f"depth-6 write = {d6_w.per_op_ms:.3f}ms "
            f"({d6_w.per_op_ms / d2_w.per_op_ms:.1f}x)"
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
