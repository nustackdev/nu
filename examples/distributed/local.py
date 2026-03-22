#!/usr/bin/env python3
"""Distributed execution on a single machine.

3 Ray actor workers, shared RocksDB, parallel execution.
Everything runs locally - no cluster needed.

    python examples/distributed/local.py
"""

from __future__ import annotations

import eb_virtuals as ebv
from eb_distributed import (
    NavigatorSpec,
    RocksDBStorageSpec,
    Teleport,
    distributed,
)
from everybase.abc import ForRange, Parallel, Print, Seq
from everybase.shape import Shape


class Market(Shape):
    btc = ebv.FloatRef.slot()
    eth = ebv.FloatRef.slot()
    sol = ebv.FloatRef.slot()


FLOW = Seq(
    Teleport(
        ebv.Transaction(
            Market.btc.store(0),
            Market.eth.store(0),
            Market.sol.store(0),
        ),
        worker=0,
    ),
    Parallel(
        Teleport(
            ForRange(
                0,
                100,
                ebv.Transaction(
                    Market.btc.store(71000.21),
                    Print("[worker 0] btc", Market.btc),
                ),
            ),
            worker=0,
        ),
        Teleport(
            ForRange(
                0,
                100,
                ebv.Transaction(
                    Market.eth.store(2700.3),
                    Print("[worker 1] eth", Market.eth),
                ),
            ),
            worker=1,
        ),
        Teleport(
            ForRange(
                0,
                100,
                ebv.Transaction(
                    Market.sol.store(70.3),
                    Print("[worker 2] sol", Market.sol),
                ),
            ),
            worker=2,
        ),
    ),
)


async def main() -> None:
    import shutil
    import tempfile

    import ray
    from composables import Runtime

    ray.init()

    db_path = tempfile.mkdtemp(prefix="eb-rocksdb-")

    try:
        async with Runtime() as rt:
            ctx = await distributed(
                rt,
                NavigatorSpec(storage_resource=RocksDBStorageSpec(path=db_path)),
                workers=3,
            )
            await FLOW.execute(ctx)
    finally:
        shutil.rmtree(db_path, ignore_errors=True)
        ray.shutdown()

    print("\nDone. 3 workers, shared RocksDB, single machine.")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
