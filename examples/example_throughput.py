"""Tree deformations — swap standard morphisms for faster PV primitives."""

from __future__ import annotations

import everypv as pv
from everybase.abc import Seq
from everypv import Snapshot, Transaction, optimize_primitive_reads, optimize_primitive_writes
from everyshape import Shape


class Record(Shape):
    a = pv.IntRef.slot()
    b = pv.IntRef.slot()
    c = pv.IntRef.slot()
    d = pv.IntRef.slot()


FIELDS = [Record.a, Record.b, Record.c, Record.d]
N = 25_000


write_flow = Transaction(
    Seq(
        *[f.set(i) for i in range(N) for f in FIELDS],
    )
)
read_flow = Snapshot(
    Seq(
        *[f.get() for i in range(N) for f in FIELDS],
    )
)


async def main() -> None:
    """Run."""
    import shutil
    import tempfile
    import time

    from tkv.tkv.storage import StorageProtocol

    from everybase import Context
    from everypv.adapters.storage import rocksdb_storage_inmemory

    total = N * len(FIELDS)
    variants = [
        ("baseline", write_flow, read_flow),
        ("optimized", optimize_primitive_writes(write_flow), optimize_primitive_reads(read_flow)),
    ]

    for label, wt, rt in variants:
        tmpdir = tempfile.mkdtemp(prefix="tp_")
        try:
            with rocksdb_storage_inmemory(tmpdir) as storage:
                ctx = Context().with_handle(StorageProtocol, storage)

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
