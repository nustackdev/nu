"""Topology presets - ready-to-use setups. Same tree runs on any preset.

# local - everything in one process
ctx = await local(runtime, NavigatorSpec())

# distributed - Ray actors across machines (see ray/presets.py)
ctx = await distributed(runtime, NavigatorSpec(), workers={"red": 2, "blue": 2})
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase import Context

from .context import ContextSpec
from .worker import Worker, WorkerSpec


if TYPE_CHECKING:
    from composables import Runtime

    from .storage import NavigatorSpec


__all__ = [
    "local",
]


async def local(runtime: Runtime, nav_spec: NavigatorSpec, *, workers: int = 2) -> Context:
    """Single process, local storage. Simplest setup.

    Everything runs in the caller's process. No RPC, no subprocesses.
    Each worker gets its own Navigator and storage instance.

    Args:
        runtime: Composables Runtime (caller manages lifecycle via async with).
        nav_spec: Navigator specification (storage backend, codec, etc.).
        workers: Number of workers (default 2).

    Returns:
        Context with N Workers bound at indices 0..N-1.
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
