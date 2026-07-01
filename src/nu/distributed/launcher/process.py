"""Ray processes - @ray.remote actors that host composables Resources.

Two actors, one generic and one everybase-specialized:

    RayProcess: receives any Spec, creates the Resource, manages lifecycle.
        Used for services (Navigator + InvisiblesServer, etc).

    WorkerProcess(RayProcess): inherits lifecycle, adds execute(tree)
        for everybase tree dispatch.

Both share a common base (_ProcessBase) for lifecycle logic.
The Spec determines what gets created - the actor is just a host.
"""

from __future__ import annotations

import asyncio
import contextlib

import ray


class _ProcessBase:
    """Shared lifecycle logic for Ray processes."""

    def __init__(self) -> None:
        self._runtime = None
        self._resource = None
        self._inflight: set[asyncio.Task] = set()

    async def start(self, spec: object) -> None:
        """Create a composables Resource from the given Spec."""
        import nu.distributed  # noqa: F401 - registers value types
        from composables import Runtime

        self._runtime = Runtime()
        await self._runtime.__aenter__()
        self._resource = await self._runtime.create(spec)

    async def shutdown(self) -> None:
        """Stop the Runtime and release all resources.

        Cancels any in-flight `aexecute` first and waits for it to unwind
        before tearing the Runtime down. Closing storage resources under a
        live flow is a use-after-free: a Nu query thread mid-RocksDB op while
        `storage.close()` aborts the transaction segfaults rdbpy.
        """
        for task in list(self._inflight):
            task.cancel()
        for task in list(self._inflight):
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await task
        self._inflight.clear()
        if self._runtime is not None:
            await self._runtime.__aexit__(None, None, None)
            self._runtime = None
            self._resource = None


@ray.remote
class RayProcess(_ProcessBase):
    """Generic Ray actor. Receives a Spec, creates a Resource."""


@ray.remote
class WorkerProcess(_ProcessBase):
    """Everybase worker Ray actor. Inherits lifecycle, adds tree execution."""

    async def aexecute(self, tree: object) -> object:
        """Execute an everybase tree against this worker's Context.

        The running task is registered so `shutdown` can cancel and drain it
        before resources (storage) are closed.
        """
        task = asyncio.current_task()
        if task is not None:
            self._inflight.add(task)
        try:
            return await self._resource.aexecute(tree)
        finally:
            if task is not None:
                self._inflight.discard(task)
