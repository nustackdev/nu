#!/usr/bin/env python3
"""
Same tree, different topologies. One line switches between local and distributed.

    local   - single process, in-memory storage
    outpost - 3 processes, shared RocksDB, 2 workers
"""

from __future__ import annotations

import eb_virtuals as ebv
from eb_distributed import (
    NavigatorSpec,
    RocksDBStorageSpec,
    Teleport,
    outpost,
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
            Market.btc.store(1),
            Market.eth.store(1),
            Market.sol.store(1),
        ),
        worker=0,
    ),
    Parallel(
        Teleport(
            ForRange(
                0,
                250,
                ebv.Transaction(
                    Market.btc.store(71000.21),
                    Print("[worker 0] price", Market.btc),
                ),
            ),
            worker=0,
        ),
        Teleport(
            ForRange(
                0,
                250,
                ebv.Transaction(
                    Market.eth.store(2700.3),
                    Print("[worker 1] price", Market.eth),
                ),
            ),
            worker=1,
        ),
        Teleport(
            ForRange(
                0,
                250,
                ebv.Transaction(
                    Market.sol.store(70.3),
                    Print("[worker 2] price", Market.sol),
                ),
            ),
            worker=2,
        ),
    ),
)


async def main():
    import shutil
    import tempfile

    from composables import Runtime

    db_path = tempfile.mkdtemp(prefix="eb-rocksdb-")

    try:
        async with Runtime() as rt:
            ctx = await outpost(
                rt,
                NavigatorSpec(storage_resource=RocksDBStorageSpec(path=db_path)),
                workers=3,
            )
            await FLOW.execute(ctx)
    finally:
        shutil.rmtree(db_path, ignore_errors=True)

    print("\nSame tree. Same flow. Different topology.")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
