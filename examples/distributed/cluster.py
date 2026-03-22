#!/usr/bin/env python3
"""Distributed execution across red and blue.

2 workers on red, 1 worker on blue, shared RocksDB via NFS.
Requires Ray cluster running on red (head) and blue (worker).

Run from red:
    cd ~/Projects/everyabc/everybase
    .venv/bin/python examples/distributed/cluster.py

Teleport routes by node+index tags:
    worker=("red", 0)   -> first worker on red
    worker=("red", 1)   -> second worker on red
    worker=("blue", 0)  -> first worker on blue
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
    # Init on red:0
    Teleport(
        ebv.Transaction(
            Market.btc.store(0),
            Market.eth.store(0),
            Market.sol.store(0),
        ),
        worker=("red", 0),
    ),
    # Parallel across both machines
    Parallel(
        Teleport(
            ForRange(
                0,
                100,
                ebv.Transaction(
                    Market.btc.store(71000.21),
                    Print("[red:0] btc", Market.btc),
                ),
            ),
            worker=("red", 0),
        ),
        Teleport(
            ForRange(
                0,
                100,
                ebv.Transaction(
                    Market.eth.store(2700.3),
                    Print("[red:1] eth", Market.eth),
                ),
            ),
            worker=("red", 1),
        ),
        Teleport(
            ForRange(
                0,
                100,
                ebv.Transaction(
                    Market.sol.store(70.3),
                    Print("[blue:0] sol", Market.sol),
                ),
            ),
            worker=("blue", 0),
        ),
    ),
)

# Packages for Ray workers (absolute paths, same on all machines via syncthing)
_EB = "/home/gor/Projects/everyabc"
_EXT = f"{_EB}/everybase/ext"
RUNTIME_PACKAGES = [
    # core
    f"{_EB}/everybase/src",
    f"{_EB}/composables",
    f"{_EB}/invisibles",
    f"{_EB}/virtuals",
    f"{_EB}/virtuals/lib/binary-codec",
    # extensions
    f"{_EXT}/eb-distributed",
    f"{_EXT}/eb-virtuals",
    f"{_EXT}/eb-dict",
    f"{_EXT}/eb-datetime",
    f"{_EXT}/eb-fin",
    f"{_EXT}/eb-math",
    f"{_EXT}/eb-path",
    f"{_EXT}/eb-uuid",
    # external
    "rdbpython",
    "cloudpickle",
    "attrs",
]


async def main() -> None:
    from pathlib import Path

    import ray
    from composables import Runtime

    ray.init(address="auto", runtime_env={"uv": RUNTIME_PACKAGES})

    db_path = str(Path.home() / "shared" / "eb-rocksdb-cluster")

    try:
        async with Runtime() as rt:
            ctx = await distributed(
                rt,
                NavigatorSpec(storage_resource=RocksDBStorageSpec(path=db_path)),
                workers={"red": 2, "blue": 1},
                storage_node="red",
            )
            await FLOW.execute(ctx)
    finally:
        ray.shutdown()

    print("\nDone. 2 machines, 3 workers, shared RocksDB.")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
