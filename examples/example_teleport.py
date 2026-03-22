#!/usr/bin/env python3
"""
Distributed tree execution with Workers and Teleport.

Shows three modes:
1. Local - everything in one process
2. Teleport (in-process) - subtree executes on a Worker with its own storage
3. Teleport (subprocess) - Worker runs in a separate process via RPC

The tree doesn't change. Teleport moves subtrees to Workers.
Workers have their own Context (own storage, own Navigator).
"""

import asyncio

from composables import Runtime
from composables.spec import SpecBuilder

import eb_virtuals as ebv
from eb_distributed import (
    ContextSpec,
    InMemoryStorageSpec,
    InvisiblesClientSpec,
    NavigatorSpec,
    ProcessLauncherSpec,
    Teleport,
    Worker,
    WorkerSpec,
)
from everybase import Context
from everybase.abc import Print, Seq
from everybase.abc.flows.parallel import Parallel
from everybase.shape import Shape


# ============================================================================
# Shape
# ============================================================================


class Data(Shape):
    price = ebv.FloatRef.slot()
    quantity = ebv.IntRef.slot()


# ============================================================================
# Flows - pure everybase, no infra
# ============================================================================

store_flow = Seq(
    Data.price.store(42.0),
    Data.quantity.store(10),
)

read_flow = Seq(
    Print("price", Data.price),
    Print("quantity", Data.quantity),
    Print("total", Data.price * Data.quantity),
)

# Full flow: store then read
full_flow = Seq(store_flow, read_flow)

# Teleported: each subtree runs on its own worker
teleported_flow = Seq(
    Teleport(store_flow, worker=0),
    Teleport(read_flow, worker=0),
)

# Parallel teleport: two workers, independent work
parallel_teleported_flow = Parallel(
    Teleport(
        Seq(
            Data.price.store(100.0),
            Data.quantity.store(5),
            Print("[worker 0] price", Data.price),
            Print("[worker 0] quantity", Data.quantity),
        ),
        worker=0,
    ),
    Teleport(
        Seq(
            Data.price.store(200.0),
            Data.quantity.store(3),
            Print("[worker 1] price", Data.price),
            Print("[worker 1] quantity", Data.quantity),
        ),
        worker=1,
    ),
)


# ============================================================================
# Main
# ============================================================================


async def main():
    # --- 1. Local: no workers, no teleport ---
    print("=== 1. Local ===")
    async with Runtime() as runtime:
        ctx_resource = await runtime.create(ContextSpec(storage=NavigatorSpec()))
        await ebv.auto_atomic(full_flow).execute(ctx_resource.ctx)

    # --- 2. Teleport (in-process workers) ---
    print("\n=== 2. Teleport (in-process workers) ===")
    async with Runtime() as runtime:
        # Create two workers, each with their own storage
        worker_0 = await runtime.create(WorkerSpec(name="worker-0"))
        worker_1 = await runtime.create(WorkerSpec(name="worker-1"))

        # Root context just has workers bound by index
        root_ctx = Context().bind(worker_0, Worker, 0).bind(worker_1, Worker, 1)

        # Store and read on worker 0 - same storage, data persists
        await ebv.auto_atomic(teleported_flow).execute(root_ctx)

    # --- 3. Parallel teleport (in-process, independent workers) ---
    print("\n=== 3. Parallel teleport (independent workers) ===")
    async with Runtime() as runtime:
        worker_0 = await runtime.create(WorkerSpec(name="worker-0"))
        worker_1 = await runtime.create(WorkerSpec(name="worker-1"))

        root_ctx = Context().bind(worker_0, Worker, 0).bind(worker_1, Worker, 1)

        # Each worker gets its own data in its own storage
        await ebv.auto_atomic(parallel_teleported_flow).execute(root_ctx)

    # --- 4. Teleport (subprocess worker via RPC) ---
    print("\n=== 4. Teleport (subprocess worker via RPC) ===")
    socket_path = "/tmp/.sock-eb-teleport"  # noqa: S108

    # Worker spec: navigator in subprocess
    subprocess_worker_spec = WorkerSpec(
        name="worker-subprocess",
        context=ContextSpec(
            storage=(
                SpecBuilder(NavigatorSpec(storage_resource=InMemoryStorageSpec()))
                .as_proxy(InvisiblesClientSpec(transport="unix", address=socket_path))
                .with_launcher(ProcessLauncherSpec(transport="unix", address=socket_path))
                .build()
            ),
        ),
    )

    async with Runtime() as runtime:
        worker_0 = await runtime.create(subprocess_worker_spec)

        root_ctx = Context().bind(worker_0, Worker, 0)

        await ebv.auto_atomic(teleported_flow).execute(root_ctx)

    print("\nDone. Same tree, different topologies.")


if __name__ == "__main__":
    asyncio.run(main())
