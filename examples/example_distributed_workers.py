#!/usr/bin/env python3
"""
Distributed workers with shared RocksDB storage.

Architecture:
    Main Process (orchestrator, no storage)
    │
    ├── State Subprocess (RocksDB + Navigator via RPC)
    │   └── InvisiblesServer @ /tmp/.sock-eb-state
    │       └── Navigator → RocksDB
    │
    ├── Worker 0 Subprocess (connects to state as client)
    │   └── InvisiblesServer @ /tmp/.sock-eb-w0
    │       └── Worker → Context → Navigator (proxy to state)
    │
    └── Worker 1 Subprocess (connects to state as client)
        └── InvisiblesServer @ /tmp/.sock-eb-w1
            └── Worker → Context → Navigator (proxy to state)

Three processes, one RocksDB. Workers are stateless executors.
The tree doesn't know any of this - it just runs.
"""

import asyncio
import shutil
import tempfile

from composables import Runtime
from composables.spec import SpecBuilder

import eb_virtuals as ebv
from eb_distributed import (
    ContextSpec,
    InvisiblesClientSpec,
    NavigatorSpec,
    ProcessLauncherSpec,
    RocksDBStorageSpec,
    Teleport,
    Worker,
    WorkerSpec,
)
from everybase import Context
from everybase.abc import Delay, Print, Seq
from everybase.abc.flows.parallel import Parallel
from everybase.shape import Shape


# ============================================================================
# Shape
# ============================================================================


class Market(Shape):
    price = ebv.FloatRef.slot()
    volume = ebv.IntRef.slot()


# ============================================================================
# Flow - pure everybase
# ============================================================================

flow = Parallel(
    Teleport(
        ebv.Transaction(
            Seq(
                Market.price.store(99.5),
                Market.volume.store(1000),
                Print("[worker 0] price", Market.price),
                Print("[worker 0] volume", Market.volume),
                Print("[worker 0] notional", Market.price * Market.volume),
            )
        ),
        worker=0,
    ),
    Teleport(
        Seq(
            Delay(1),
            ebv.Transaction(
                Seq(
                    Market.price.store(101.2),
                    Market.volume.store(500),
                    Print("[worker 1] price", Market.price),
                    Print("[worker 1] volume", Market.volume),
                    Print("[worker 1] notional", Market.price * Market.volume),
                ),
            ),
        ),
        worker=1,
    ),
)

# After both workers finish, read from one worker to verify shared storage
verify_flow = ebv.Transaction(
    Seq(
        Print("[verify] final price", Market.price),
        Print("[verify] final volume", Market.volume),
    )
)


# ============================================================================
# Spec composition
# ============================================================================


def build_specs(db_path: str):
    state_socket = "/tmp/.sock-eb-state"  # noqa: S108
    worker_0_socket = "/tmp/.sock-eb-w0"  # noqa: S108
    worker_1_socket = "/tmp/.sock-eb-w1"  # noqa: S108

    # The real storage: RocksDB Navigator in a subprocess
    nav_spec = NavigatorSpec(
        storage_resource=RocksDBStorageSpec(path=db_path),
    )

    # State service: Navigator + RocksDB in subprocess
    # threaded executor: multiple clients (main + workers) connect concurrently
    # inline dispatcher: Navigator is sync, each connection thread runs methods inline
    state_nav_spec = (
        SpecBuilder(nav_spec)
        .as_proxy(InvisiblesClientSpec(transport="unix", address=state_socket))
        .with_launcher(
            ProcessLauncherSpec(
                transport="unix",
                address=state_socket,
                executor="threaded",
            )
        )
        .build()
    )

    # Worker nav: proxy-only to state service (no launcher - state already running)
    worker_nav_spec = (
        SpecBuilder(nav_spec)
        .as_proxy(InvisiblesClientSpec(transport="unix", address=state_socket))
        .build()
    )

    # Worker base spec: worker with context pointing to shared storage
    worker_base_spec = WorkerSpec(
        context=ContextSpec(storage=worker_nav_spec),
    )

    # Workers in subprocesses
    # simple executor: one client (main process) per worker
    # async dispatcher: Worker.execute() is async
    worker_0_spec = (
        SpecBuilder(worker_base_spec)
        .as_proxy(InvisiblesClientSpec(transport="unix", address=worker_0_socket))
        .with_launcher(
            ProcessLauncherSpec(
                transport="unix",
                address=worker_0_socket,
                dispatcher="async",
            )
        )
        .build()
    )

    worker_1_spec = (
        SpecBuilder(worker_base_spec)
        .as_proxy(InvisiblesClientSpec(transport="unix", address=worker_1_socket))
        .with_launcher(
            ProcessLauncherSpec(
                transport="unix",
                address=worker_1_socket,
                dispatcher="async",
            )
        )
        .build()
    )

    return state_nav_spec, worker_0_spec, worker_1_spec


# ============================================================================
# Main
# ============================================================================


async def main():
    db_path = tempfile.mkdtemp(prefix="eb-rocksdb-")
    print(f"RocksDB path: {db_path}")

    state_nav_spec, worker_0_spec, worker_1_spec = build_specs(db_path)

    try:
        async with Runtime() as runtime:
            # 1. Start state service (RocksDB in subprocess)
            print("Starting state service...")
            await runtime.create(state_nav_spec)
            print("State service ready.")

            # 2. Start workers (each connects to state)
            print("Starting workers...")
            worker_0 = await runtime.create(worker_0_spec)
            worker_1 = await runtime.create(worker_1_spec)
            print("Workers ready.")

            # 3. Build root context with workers
            root_ctx = Context().bind(worker_0, Worker, 0).bind(worker_1, Worker, 1)

            # 4. Execute: two branches in parallel, each on its own worker
            print("\n--- Parallel execution on 2 workers ---")
            await flow.execute(root_ctx)

            # 5. Verify: read from worker 0 (shared storage)
            print("\n--- Verify (read from worker 0, shared RocksDB) ---")
            await Teleport(verify_flow, worker=0).execute(root_ctx)

        print("\nDone. Three processes, one RocksDB, two workers.")

    finally:
        shutil.rmtree(db_path, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(main())
