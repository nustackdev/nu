#!/usr/bin/env python3
"""Reactive execution - writer and reactive reader on shared storage.

Worker 0 writes counter values. Worker 1 reacts to changes and prints.
Uses Race to run both concurrently - writer finishes, Race cancels reader.

STATUS: NOT WORKING YET. Requires background serve thread on InvisiblesClient
so the server can call back into the worker via NetRef callbacks. Currently
the worker's connection only serves during sync_request waits (reentrant),
not during asyncio Event waits. See RPyC's BgServingThread for the pattern.

    python examples/distributed/reactive.py
"""

from __future__ import annotations

import asyncio
import shutil
import socket
import tempfile

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
    RocksDBStorageSpec,
    Teleport,
    Worker,
    WorkerSpec,
)
from everybase import Context
from everybase.abc import Delay, ForRange, Print, Race, Seq
from everybase.shape import Shape
from everybase.shape.flows.reactive import ReactWhile


# -- Shape -------------------------------------------------------------------


class State(Shape):
    counter = ebv.IntRef.slot()
    index = ebv.IntRef.slot()


# -- Flow --------------------------------------------------------------------

flow = Race(
    # writer: increment counter 20 times with small delay
    Teleport(
        ebv.Transaction(
            ForRange(
                0,
                20,
                Seq(
                    State.counter.store(State.counter + 1),
                    Print("write | counter", State.counter),
                    Delay(0.1),
                ),
                index=State.index,
            ),
        ),
        worker=0,
    ),
    # reader: react to counter changes, print until counter >= 15
    Teleport(
        ebv.Transaction(
            ReactWhile(
                State.counter.on_change(),
                State.counter < 15,
                Print("react | counter changed to", State.counter),
            ),
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
            # shared storage service
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

            # 2 workers: writer and reader
            proxy_nav = (
                SpecBuilder(nav_spec)
                .as_proxy(InvisiblesClientSpec(transport="tcp", address=address))
                .build()
            )

            ctx = Context()
            for i in range(2):
                w = await rt.create(
                    RayWorkerSpec(
                        name=f"worker-{i}",
                        inner_spec=WorkerSpec(context=ContextSpec(storage=proxy_nav)),
                        actor_name=f"eb-worker-{i}",
                    )
                )
                ctx = ctx.bind(w, Worker, i)

            # init counter before starting
            await Teleport(
                ebv.Transaction(State.counter.store(0)),
                worker=0,
            ).execute(ctx)

            await flow.execute(ctx)

    finally:
        shutil.rmtree(db_path, ignore_errors=True)
        ray.shutdown()

    print("\ndone. writer + reactive reader, shared rocksdb.")


if __name__ == "__main__":
    asyncio.run(main())
