"""Throughput demo — fast writes and reads through the Shape term system.

Builds term trees for writing and reading Shape fields, executed under
a single Transaction (writes) or Snapshot (reads).

Uses unsafe primitive writes (InitCmd + ItemPrimitiveSetUnsafeCmd)
which skip redundant validation reads — safe because the Shape schema
guarantees field types at definition time.

Uses:
  everyshape     → Shape, InitCmd, ItemPrimitiveSetUnsafeCmd
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
from everybase.abc.utils import ensure_term
from everypv import Snapshot, Transaction
from everyshape import Shape
from everyshape.morphisms.item import InitCmd, ItemPrimitiveSetUnsafeCmd


# ── Shape ─────────────────────────────────────────────────────────────


class Record(Shape):
    a = pv.IntRef.slot()
    b = pv.IntRef.slot()
    c = pv.IntRef.slot()
    d = pv.IntRef.slot()


FIELDS = [Record.a, Record.b, Record.c, Record.d]
N = 25_000
TOTAL = N * len(FIELDS)

# ── Trees ─────────────────────────────────────────────────────────────

writes = Transaction(
    Seq(
        # Materialize containers once
        *[InitCmd(f) for f in FIELDS],
        # Then raw writes — no validation, no ensure_created
        *[ItemPrimitiveSetUnsafeCmd(f, ensure_term(i)) for i in range(N) for f in FIELDS],
    ),
    scope=Record,
)

reads = Snapshot(
    Seq(*[f.get() for i in range(N) for f in FIELDS]),
    scope=Record,
)


# ── Run ───────────────────────────────────────────────────────────────


def report(label: str, elapsed: float, n: int) -> None:
    us = (elapsed / n) * 1_000_000
    ops = n / elapsed
    print(f"  {label:<8s} {elapsed:>7.3f}s    {us:>5.1f} us/op    {ops:>10,.0f} ops/sec")


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

    print(f"\n  {TOTAL:,} Shape field ops ({N:,} records x {len(FIELDS)} fields)\n")
    report("writes", t_write, TOTAL)
    report("reads", t_read, TOTAL)
    print()


if __name__ == "__main__":
    asyncio.run(main())
