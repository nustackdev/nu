#!/usr/bin/env python3
"""Multiprocess execution - Ray on a single machine, shared RocksDB.

Workers run as Ray actors in separate processes. All share one RocksDB
through an invisibles storage service. Any worker can read what others wrote.

    python examples/distributed/multiprocess.py
"""

from __future__ import annotations

import asyncio
import shutil
import socket
import tempfile

import ray
from composables import Runtime
from composables.spec import SpecBuilder

import nu_virtuals as ebv
from nu_distributed import (
    ContextSpec,
    InvisiblesClientSpec,
    InvisiblesServerSpec,
    NavigatorSpec,
    RayActorSpec,
    RayWorkerSpec,
    RocksDBStorageSpec,
    Teleport,
    Worker,
    WorkerSpec,
)
from nu import Context
from nu.abc import ForRange, If, Parallel, Print, Seq
from nu.shape import Shape


# -- Shape -------------------------------------------------------------------


class Counter(Shape):
    value = ebv.IntRef.slot()
    index = ebv.IntRef.slot()


class Counters(Shape):
    items = ebv.ShapesDictRef.slot(Counter)


# refs into each counter - isolated value + index per key
a = Counters.items["a"]
b = Counters.items["b"]
c = Counters.items["c"]


# -- Flow --------------------------------------------------------------------

flow = Seq(
    # init shared state
    Teleport(
        ebv.Transaction(
            a.value.store(0),
            b.value.store(0),
            c.value.store(0),
        ),
        worker=0,
    ),
    # 3 workers increment in parallel, print every 10 iterations
    Parallel(
        Teleport(
            ebv.Transaction(
                ForRange(
                    0,
                    100,
                    Seq(
                        a.value.store(a.value + 1),
                        If((a.index % 10).eq(0), Print("worker 0 | a", a.value)),
                    ),
                    index=a.index,
                )
            ),
            worker=0,
        ),
        Teleport(
            ebv.Transaction(
                ForRange(
                    0,
                    100,
                    Seq(
                        b.value.store(b.value + 1),
                        If((b.index % 10).eq(0), Print("worker 1 | b", b.value)),
                    ),
                    index=b.index,
                )
            ),
            worker=1,
        ),
        Teleport(
            ebv.Transaction(
                ForRange(
                    0,
                    100,
                    Seq(
                        c.value.store(c.value + 1),
                        If((c.index % 10).eq(0), Print("worker 2 | c", c.value)),
                    ),
                    index=c.index,
                )
            ),
            worker=2,
        ),
    ),
    # any worker can read all three - storage is shared
    Teleport(
        ebv.Snapshot(
            Print("final | a", a.value),
            Print("final | b", b.value),
            Print("final | c", c.value),
        ),
        worker=1,
    ),
)


# -- Main --------------------------------------------------------------------


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


async def main() -> None:
    ray.init()
    db_path = tempfile.mkdtemp(prefix="eb-rocksdb-")

    try:
        address = f"{ray.util.get_node_ip_address()}:{_free_port()}"
        nav_spec = NavigatorSpec(storage_resource=RocksDBStorageSpec(path=db_path))

        async with Runtime() as rt:
            # one RocksDB served over invisibles
            await rt.create(
                RayActorSpec(
                    name="storage",
                    inner_spec=InvisiblesServerSpec(
                        transport="tcp",
                        address=address,
                        executor="threaded",
                        root_service=nav_spec,
                    ),
                    actor_name="eb-storage",
                )
            )

            # 3 workers, all proxy to shared storage
            proxy_nav = (
                SpecBuilder(nav_spec)
                .as_proxy(InvisiblesClientSpec(transport="tcp", address=address))
                .build()
            )

            ctx = Context()
            for i in range(3):
                w = await rt.create(
                    RayWorkerSpec(
                        name=f"worker-{i}",
                        inner_spec=WorkerSpec(context=ContextSpec(storage=proxy_nav)),
                        actor_name=f"eb-worker-{i}",
                    )
                )
                ctx = ctx.bind(w, Worker, i)

            await flow.execute(ctx)

    finally:
        shutil.rmtree(db_path, ignore_errors=True)
        ray.shutdown()

    print("\ndone. 3 ray workers, shared rocksdb, single machine.")


if __name__ == "__main__":
    asyncio.run(main())
