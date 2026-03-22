#!/usr/bin/env python3
"""Distributed execution via Ray.

Same tree as example_presets.py, but workers are Ray actors.
Storage service runs as a Ray actor with InvisiblesServer.
Workers connect to it via invisibles for storage access,
receive trees via Ray dispatch.

All components are composables Resources managed by a single Runtime.

    python examples/example_ray.py
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
    # Initialize all refs on worker 0
    Teleport(
        ebv.Transaction(
            Market.btc.store(0),
            Market.eth.store(0),
            Market.sol.store(0),
        ),
        worker=0,
    ),
    # Parallel writes across 3 workers
    Parallel(
        Teleport(
            ForRange(
                0,
                250,
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
                250,
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
                250,
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

    print("\nSame tree. Ray actors. Distributed.")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
