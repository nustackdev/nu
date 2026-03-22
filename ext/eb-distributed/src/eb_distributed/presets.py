"""Topology presets - ready-to-use distributed setups.

Pass a NavigatorSpec, get a complete topology. Same tree runs on any preset.

    # local - everything in one process
    ctx = await local(runtime, NavigatorSpec())

    # outpost - state service + N workers in subprocesses
    ctx = await outpost(runtime, NavigatorSpec(), workers=2)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from composables.spec import SpecBuilder

from everybase import Context

from .context import ContextSpec
from .launcher.process import ProcessLauncherSpec
from .rpc.client import InvisiblesClientSpec
from .worker import Worker, WorkerSpec


if TYPE_CHECKING:
    from composables import Runtime

    from .storage import NavigatorSpec


__all__ = [
    "local",
    "outpost",
]


async def local(runtime: Runtime, nav_spec: NavigatorSpec, *, workers: int = 2) -> Context:
    """Single process, local storage. Simplest setup.

    Everything runs in the caller's process. No RPC, no subprocesses.
    Each worker gets its own Navigator and storage instance.
    Good for development, testing, and small workloads.

    Args:
        runtime: Composables Runtime (caller manages lifecycle via async with)
        nav_spec: Navigator specification (storage backend, codec, etc.)
        workers: Number of workers (default 2)

    Returns:
        Context with N Workers bound at indices 0..N-1
    """
    ctx = Context()
    for i in range(workers):
        worker = await runtime.create(
            WorkerSpec(
                name=f"worker-{i}",
                context=ContextSpec(storage=nav_spec),
            )
        )
        ctx = ctx.bind(worker, Worker, i)
    return ctx


async def outpost(
    runtime: Runtime,
    nav_spec: NavigatorSpec,
    *,
    workers: int = 2,
    base_socket: str = "/tmp/.eb",  # noqa: S108
) -> Context:
    """Distributed setup: shared state service + N worker subprocesses.

    Architecture:
        Main Process (orchestrator)
        ├── State Subprocess (Navigator + storage via RPC, threaded)
        ├── Worker 0 Subprocess (connects to state, async dispatcher)
        ├── Worker 1 Subprocess (connects to state, async dispatcher)
        └── ...

    All workers share the same storage through the state service.
    The tree doesn't know any of this.

    Args:
        runtime: Composables Runtime (caller manages lifecycle via async with)
        nav_spec: Navigator specification (storage backend, codec, etc.)
        workers: Number of worker subprocesses (default 2)
        base_socket: Base path for unix sockets (suffixed with -state, -w0, etc.)

    Returns:
        Context with N Workers bound at indices 0..N-1
    """
    state_sock = f"{base_socket}-state"

    # State service: Navigator in subprocess, threaded executor for multiple clients
    state_spec = (
        SpecBuilder(nav_spec)
        .as_proxy(InvisiblesClientSpec(transport="unix", address=state_sock))
        .with_launcher(
            ProcessLauncherSpec(
                transport="unix",
                address=state_sock,
                executor="threaded",
            )
        )
        .build()
    )

    # Worker nav: proxy-only to state (no launcher - state already running)
    worker_nav = (
        SpecBuilder(nav_spec)
        .as_proxy(InvisiblesClientSpec(transport="unix", address=state_sock))
        .build()
    )

    worker_base = WorkerSpec(context=ContextSpec(storage=worker_nav))

    # Start state service first
    await runtime.create(state_spec)

    # Start workers
    ctx = Context()
    for i in range(workers):
        w_sock = f"{base_socket}-w{i}"
        w_spec = (
            SpecBuilder(worker_base)
            .as_proxy(InvisiblesClientSpec(transport="unix", address=w_sock))
            .with_launcher(
                ProcessLauncherSpec(
                    transport="unix",
                    address=w_sock,
                    dispatcher="async",
                )
            )
            .build()
        )
        worker = await runtime.create(w_spec)
        ctx = ctx.bind(worker, Worker, i)

    return ctx
