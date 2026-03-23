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

import ray


class _ProcessBase:
    """Shared lifecycle logic for Ray processes."""

    def __init__(self) -> None:
        self._runtime = None
        self._resource = None

    async def start(self, spec: object) -> None:
        """Create a composables Resource from the given Spec."""
        from composables import Runtime

        import eb_distributed  # noqa: F401 - registers value types

        self._runtime = Runtime()
        await self._runtime.__aenter__()
        self._resource = await self._runtime.create(spec)

    async def shutdown(self) -> None:
        """Stop the Runtime and release all resources."""
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

    async def execute(self, tree: object) -> object:
        """Execute an everybase tree against this worker's Context."""
        return await self._resource.execute(tree)
