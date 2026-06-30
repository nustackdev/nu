#!/usr/bin/env python3
"""Iteration micro-benchmark.

Pure ForEachDo + IfDo dispatch cost. No state, no storage, no RPC.
Print only on the matched branch (every 3rd item).

Usage:
    python examples/bench_iteration.py --n 1500
"""

from __future__ import annotations

import argparse
import asyncio
import time

import nu
from nu import runtime


def build_app(n: int) -> nu.Nu:
    items = [{"tx_id": i, "match": (i % 1000) == 0} for i in range(n)]
    matched = nu.At(nu.DictAttrRef("tx"), "match")

    return nu.ForEachDo(
        items,
        nu.IfDo(
            nu.ToBool(matched),
            nu.Print("matched", nu.At(nu.DictAttrRef("tx"), "tx_id")),
        ),
        item="tx",
    )


async def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=1500)
    p.add_argument("--repeats", type=int, default=3)
    args = p.parse_args()

    app = build_app(args.n)
    ctx = nu.Context()

    for r in range(args.repeats):
        t0 = time.perf_counter()
        await runtime.aexecute(app, ctx)
        elapsed = time.perf_counter() - t0
        print(
            f"run {r + 1}/{args.repeats}: n={args.n} elapsed={elapsed:.3f}s "
            f"throughput={args.n / elapsed:.0f} tx/s"
        )


if __name__ == "__main__":
    asyncio.run(main())
