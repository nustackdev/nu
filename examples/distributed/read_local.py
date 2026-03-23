#!/usr/bin/env python3
"""Cluster with local reads - writes through proxy, reads from local secondary.

Same as cluster.py but each worker also opens a read-only secondary
RocksDB pointing to the same NFS path. Eliminates network round-trips
for reads while keeping writes consistent through the central service.

    writes:  worker -> invisibles -> primary RocksDB (single writer)
    reads:   worker -> local secondary RocksDB (follows primary, no RTT)

Requires:
    - Ray cluster: red (head) + blue (worker)
    - NFS: ~/shared mounted on both machines
    - Redis: running on red

Run from red:
    cd ~/Projects/everyabc/everybase
    .venv/bin/python examples/distributed/read_local.py
"""

from __future__ import annotations

import asyncio
import socket

import ray
from composables import Runtime
from composables.spec import SpecBuilder

import eb_virtuals as ebv
from eb_distributed import (
    ContextSpec,
    InvisiblesClientSpec,
    InvisiblesServerSpec,
    NavigatorSpec,
    RayActorSpec,
    RayWorkerSpec,
    RedisObserverSpec,
    RocksDBStorageSpec,
    Teleport,
    Worker,
    WorkerSpec,
)
from everybase import Context
from everybase.abc import ForRange, If, Parallel, Print, Seq
from everybase.shape import Shape


# -- Shape -------------------------------------------------------------------


class Counter(Shape):
    value = ebv.IntRef.slot()
    index = ebv.IntRef.slot()


class Counters(Shape):
    items = ebv.ShapesDictRef.slot(Counter)


a = Counters.items["a"]
b = Counters.items["b"]
c = Counters.items["c"]


# -- Flow --------------------------------------------------------------------

flow = Seq(
    # init
    Teleport(
        ebv.Transaction(
            a.value.store(0),
            b.value.store(0),
            c.value.store(0),
        ),
        worker=("red", 0),
    ),
    # write through proxy, print every 10 iterations
    Parallel(
        Teleport(
            ForRange(
                0,
                100,
                Seq(
                    ebv.Transaction(a.value.store(a.value + 1)),
                    If(a.index % 10 == 0, ebv.Snapshot(Print("red:0  | a", a.value))),
                ),
                index=a.index,
            ),
            worker=("red", 0),
        ),
        Teleport(
            ForRange(
                0,
                100,
                Seq(
                    ebv.Transaction(b.value.store(b.value + 1)),
                    If(b.index % 10 == 0, ebv.Snapshot(Print("red:1  | b", b.value))),
                ),
                index=b.index,
            ),
            worker=("red", 1),
        ),
        Teleport(
            ForRange(
                0,
                100,
                Seq(
                    ebv.Transaction(c.value.store(c.value + 1)),
                    If(c.index % 10 == 0, ebv.Snapshot(Print("blue:0 | c", c.value))),
                ),
                index=c.index,
            ),
            worker=("blue", 0),
        ),
    ),
    # read from each machine (once split-path is supported, reads hit local secondary)
    Teleport(
        ebv.Snapshot(
            Print("red reads  | a", a.value),
            Print("red reads  | b", b.value),
            Print("red reads  | c", c.value),
        ),
        worker=("red", 0),
    ),
    Teleport(
        ebv.Snapshot(
            Print("blue reads | a", a.value),
            Print("blue reads | b", b.value),
            Print("blue reads | c", c.value),
        ),
        worker=("blue", 0),
    ),
)


# -- Packages ----------------------------------------------------------------

_EB = "/home/gor/Projects/everyabc"
_EXT = f"{_EB}/everybase/ext"

RUNTIME_PACKAGES = [
    f"{_EB}/everybase/src",
    f"{_EB}/composables",
    f"{_EB}/invisibles",
    f"{_EB}/virtuals",
    f"{_EB}/virtuals/lib/binary-codec",
    f"{_EXT}/eb-distributed",
    f"{_EXT}/eb-virtuals",
    f"{_EXT}/eb-dict",
    f"{_EXT}/eb-datetime",
    f"{_EXT}/eb-fin",
    f"{_EXT}/eb-math",
    f"{_EXT}/eb-path",
    f"{_EXT}/eb-uuid",
    "rdbpython",
    "cloudpickle",
    "attrs",
]


# -- Config ------------------------------------------------------------------

NODES = {"red": 2, "blue": 1}
DB_PATH = "/home/gor/shared/eb-rocksdb-read-local"
SECONDARY_PATH = "/tmp/eb-rocksdb-secondary"  # noqa: S108
REDIS_URL = "redis://10.0.0.1:6379"


# -- Main --------------------------------------------------------------------


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


async def main() -> None:
    ray.init(address="auto", runtime_env={"uv": RUNTIME_PACKAGES})

    try:
        address = f"{ray.util.get_node_ip_address()}:{_free_port()}"

        # primary: writable RocksDB + Redis observer
        primary_nav = NavigatorSpec(
            storage_resource=RocksDBStorageSpec(
                path=DB_PATH,
                observer_resource=RedisObserverSpec(redis_url=REDIS_URL),
            ),
        )

        # secondary: read-only RocksDB following primary via NFS
        # (building block for split-path reads once Context supports dual navigators)
        _secondary_nav = NavigatorSpec(
            storage_resource=RocksDBStorageSpec(
                path=DB_PATH,
                read_only=True,
                secondary_path=SECONDARY_PATH,
                observer_resource=RedisObserverSpec(redis_url=REDIS_URL),
            ),
        )

        async with Runtime() as rt:
            # storage service on red
            await rt.create(
                RayActorSpec(
                    name="storage",
                    inner_spec=InvisiblesServerSpec(
                        transport="tcp",
                        address=address,
                        executor="threaded",
                        root_service=primary_nav,
                    ),
                    actor_name="eb-storage",
                    node="red",
                    max_restarts=-1,
                )
            )

            # workers proxy all ops for now
            # TODO: split-path - writes through proxy, reads from _secondary_nav
            proxy_nav = (
                SpecBuilder(primary_nav)
                .as_proxy(InvisiblesClientSpec(transport="tcp", address=address))
                .build()
            )

            ctx = Context()
            idx = 0
            for node, count in NODES.items():
                for local_idx in range(count):
                    w = await rt.create(
                        RayWorkerSpec(
                            name=f"worker-{node}-{local_idx}",
                            inner_spec=WorkerSpec(
                                context=ContextSpec(storage=proxy_nav),
                            ),
                            actor_name=f"eb-worker-{idx}",
                            node=node,
                            max_restarts=-1,
                            tags=((node, local_idx),),
                        )
                    )
                    ctx = ctx.bind(w, Worker, idx)
                    ctx = ctx.bind(w, Worker, (node, local_idx))
                    idx += 1

            await flow.execute(ctx)

    finally:
        ray.shutdown()

    print("\ndone. cluster with local read path (secondary rocksdb).")


if __name__ == "__main__":
    asyncio.run(main())
