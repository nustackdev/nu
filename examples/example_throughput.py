"""Throughput demo — 100K writes and reads through the Shape term system.

Builds two term trees (one write, one read), each containing 100K
operations batched under a single Transaction/Snapshot span.

Trees are built once, executed once. This measures pure execution
throughput — the ceiling for batched Shape field access.

Uses:
  everyshape     → Shape definition
  everypv        → Ref slots, Transaction/Snapshot spans
  everybase.abc  → Seq (sequential composition)
"""

from __future__ import annotations

import asyncio
import shutil
import tempfile
import time

import everypv as pv
from everybase import Context
from everybase.abc import Seq
from everypv import Snapshot, Transaction
from everyshape import Shape


# ── Shape ─────────────────────────────────────────────────────────────


class Record(Shape):
    value = pv.IntRef.slot()


# ── Trees ─────────────────────────────────────────────────────────────

N = 100_000

writes = Transaction(Seq(*[Record.value.set(i) for i in range(N)]), scope=Record)
reads = Snapshot(Seq(*[Record.value.get() for _ in range(N)]), scope=Record)


# ── Run ───────────────────────────────────────────────────────────────


def report(label: str, elapsed: float, n: int) -> None:
    us = (elapsed / n) * 1_000_000
    ops = n / elapsed
    print(f"  {label:<12s} {elapsed:>8.3f}s    {us:>6.1f} us/op    {ops:>10,.0f} ops/sec")


async def main() -> None:
    from tkv.tkv.storage import StorageProtocol

    from everypv.adapters.storage import rocksdb_storage_inmemory

    tmpdir = tempfile.mkdtemp(prefix="throughput_")
    try:
        with rocksdb_storage_inmemory(tmpdir) as storage:
            ctx = Context().with_handle(StorageProtocol, storage)

            t0 = time.perf_counter()
            await writes.execute(ctx)
            t_write = time.perf_counter() - t0

            t0 = time.perf_counter()
            await reads.execute(ctx)
            t_read = time.perf_counter() - t0
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print(f"\n  {N:,} Shape field ops — single span, batched\n")
    report("writes", t_write, N)
    report("reads", t_read, N)
    print()


if __name__ == "__main__":
    asyncio.run(main())
