"""Ray topology presets - distributed setups via Ray actors.

One function switches between single-node and multi-machine. Same tree.

    # single node, 4 workers
    ctx = await distributed(runtime, NavigatorSpec(), workers=4)

    # multi-machine: 2 workers on red, 2 on blue
    ctx = await distributed(runtime, NavigatorSpec(), workers={"red": 2, "blue": 2})
"""

from __future__ import annotations

import socket
from typing import TYPE_CHECKING

from .resource import RayActorSpec, RayWorkerSpec


if TYPE_CHECKING:
    from composables import Runtime

    from everybase import Context

    from ..storage import NavigatorSpec


__all__ = [
    "distributed",
]


def _find_free_port() -> int:
    """Find a free TCP port on this machine."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


async def distributed(
    runtime: Runtime,
    nav_spec: NavigatorSpec,
    *,
    workers: int | dict[str, int] = 2,
    storage_address: str | None = None,
) -> Context:
    """Distributed setup: storage service + N workers via Ray actors.

    Architecture:
        Ray Cluster
        ├── RayProcess (Navigator + InvisiblesServer, no factory)
        ├── WorkerProcess 0 (Worker + Navigator proxy → service)
        ├── WorkerProcess 1 (Worker + Navigator proxy → service)
        └── ...

    All components are composables Resources managed by the Runtime.
    Workers connect to the storage service via invisibles (TCP) for
    high-frequency storage access. Trees arrive via Ray dispatch.

    Args:
        runtime: Composables Runtime (caller manages lifecycle via async with).
        nav_spec: Navigator specification (storage backend, codec, etc.).
        workers: Number of workers (int) or per-node placement (dict).
            int: N workers on any available node.
            dict: {"red": 2, "blue": 2} → 2 workers on each node.
        storage_address: TCP address for the storage service.
            If None, auto-selects a free port.

    Returns:
        Context with N Workers bound at sequential indices 0..N-1.
    """
    import ray
    from composables.spec import SpecBuilder

    from everybase import Context

    from ..context import ContextSpec
    from ..rpc.client import InvisiblesClientSpec
    from ..rpc.server import InvisiblesServerSpec
    from ..worker import Worker, WorkerSpec

    # Resolve storage address
    if storage_address is None:
        port = _find_free_port()
        host = ray.util.get_node_ip_address()
        storage_address = f"{host}:{port}"

    # --- Service: Navigator as root of InvisiblesServer (no factory) ---
    await runtime.create(
        RayActorSpec(
            name="storage-service",
            inner_spec=InvisiblesServerSpec(
                transport="tcp",
                address=storage_address,
                executor="threaded",
                root_service=nav_spec,
            ),
        )
    )

    # --- Workers: each with direct proxy to Navigator (no factory) ---
    worker_nav = (
        SpecBuilder(nav_spec)
        .as_proxy(
            InvisiblesClientSpec(
                transport="tcp",
                address=storage_address,
            )
        )
        .build()
    )

    ctx = Context()
    idx = 0

    if isinstance(workers, int):
        for _ in range(workers):
            worker = await runtime.create(
                RayWorkerSpec(
                    name=f"worker-{idx}",
                    inner_spec=WorkerSpec(context=ContextSpec(storage=worker_nav)),
                )
            )
            ctx = ctx.bind(worker, Worker, idx)
            idx += 1
    else:
        for node, count in workers.items():
            for _ in range(count):
                worker = await runtime.create(
                    RayWorkerSpec(
                        name=f"worker-{node}-{idx}",
                        inner_spec=WorkerSpec(context=ContextSpec(storage=worker_nav)),
                        node=node,
                    )
                )
                ctx = ctx.bind(worker, Worker, idx)
                idx += 1

    return ctx
