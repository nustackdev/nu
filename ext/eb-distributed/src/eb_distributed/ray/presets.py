"""Ray topology presets - distributed setups via Ray actors.

One function switches between single-node and multi-machine. Same tree.

    # single node, 4 workers
    ctx = await distributed(runtime, NavigatorSpec(), workers=4)

    # multi-machine: 2 workers on red, 2 on blue
    ctx = await distributed(runtime, NavigatorSpec(), workers={"red": 2, "blue": 2})

    # with fault tolerance
    ctx = await distributed(runtime, NavigatorSpec(), workers=4, max_restarts=-1)
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
    storage_node: str | None = None,
    max_restarts: int = 0,
) -> Context:
    """Distributed setup: storage service + N workers via Ray actors.

    Architecture:
        Ray Cluster
        ├── RayProcess "storage" (Navigator + InvisiblesServer)
        ├── WorkerProcess "worker-0" (Worker + Navigator proxy → storage)
        ├── WorkerProcess "worker-1" (Worker + Navigator proxy → storage)
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
        storage_node: Place storage service on a specific Ray node.
        max_restarts: Max restarts on actor failure. 0=none, -1=infinite.

    Returns:
        Context with N Workers bound at sequential indices 0..N-1.
    """
    import ray
    from composables.spec import SpecBuilder

    from everybase import Context

    from ..context import ContextSpec
    from ..rpc.client import InvisiblesClientSpec
    from ..rpc.server import InvisiblesServerSpec
    from ..worker import WorkerSpec

    # Resolve storage address
    if storage_address is None:
        port = _find_free_port()
        host = ray.util.get_node_ip_address()
        storage_address = f"{host}:{port}"

    # --- Storage service: Navigator as root of InvisiblesServer ---
    await runtime.create(
        RayActorSpec(
            name="storage-service",
            inner_spec=InvisiblesServerSpec(
                transport="tcp",
                address=storage_address,
                executor="threaded",
                root_service=nav_spec,
            ),
            actor_name="eb-storage",
            node=storage_node,
            max_restarts=max_restarts,
        )
    )

    # --- Workers: each with direct proxy to Navigator ---
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
                    actor_name=f"eb-worker-{idx}",
                    max_restarts=max_restarts,
                )
            )
            ctx = _bind_worker(ctx, worker, idx)
            idx += 1
    else:
        for node, count in workers.items():
            node_idx = 0
            for _ in range(count):
                # Auto-tag: (node, local_idx) for node+index routing
                tags: tuple = ((node, node_idx),)

                worker = await runtime.create(
                    RayWorkerSpec(
                        name=f"worker-{node}-{idx}",
                        inner_spec=WorkerSpec(context=ContextSpec(storage=worker_nav)),
                        actor_name=f"eb-worker-{idx}",
                        node=node,
                        max_restarts=max_restarts,
                        tags=tags,
                    )
                )
                ctx = _bind_worker(ctx, worker, idx)
                idx += 1
                node_idx += 1

    return ctx


def _bind_worker(ctx: object, worker: object, idx: int) -> object:
    """Bind worker to context by index + any extra tags from spec."""
    from ..worker import Worker

    # Always bind by flat index
    ctx = ctx.bind(worker, Worker, idx)

    # Bind extra tag aliases from spec
    for tag in worker.spec.tags:
        ctx = ctx.bind(worker, Worker, tag)

    return ctx
