"""Tree deformations — swap standard morphisms for faster PV primitives."""

from __future__ import annotations

import eb_virtuals as ebv
from eb_virtuals import Snapshot, Transaction, optimize_primitive_reads, optimize_primitive_writes
from everybase.abc import Seq
from everybase.shape import Shape


class Record(Shape):
    a = ebv.IntRef.slot()
    b = ebv.IntRef.slot()
    c = ebv.IntRef.slot()
    d = ebv.IntRef.slot()


FIELDS = [Record.a, Record.b, Record.c, Record.d]
N = 25_000


write_flow = Transaction(
    Seq(
        *[f.store(i) for i in range(N) for f in FIELDS],
    )
)
read_flow = Snapshot(
    Seq(
        *[f for i in range(N) for f in FIELDS],
    )
)


async def main() -> None:
    """Run."""
    import shutil
    import tempfile
    import time

    from virtuals.tkv.storage import StorageProtocol

    from eb_virtuals.presets import rocksdb_storage_inmemory
    from everybase import Context

    total = N * len(FIELDS)
    variants = [
        ("baseline", write_flow, read_flow),
        ("optimized", optimize_primitive_writes(write_flow), optimize_primitive_reads(read_flow)),
    ]

    for label, wt, rt in variants:
        tmpdir = tempfile.mkdtemp(prefix="tp_")
        try:
            with rocksdb_storage_inmemory(tmpdir) as storage:
                ctx = Context().bind(storage, StorageProtocol)

                t0 = time.perf_counter()
                await wt.execute(ctx)
                w = total / (time.perf_counter() - t0)

                t0 = time.perf_counter()
                await rt.execute(ctx)
                r = total / (time.perf_counter() - t0)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

        print(f"  {label:<10s}  writes {w:>8,.0f} ops/sec   reads {r:>8,.0f} ops/sec")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
