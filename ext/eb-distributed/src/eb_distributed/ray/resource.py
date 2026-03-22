"""Ray composables Resources - lifecycle wrappers for Ray processes.

Two Resources, one generic and one everybase-specialized:

    RayActor: wraps a RayProcess. Manages lifecycle (setup/cleanup).
        Used for services (Navigator + InvisiblesServer, etc).

    RayWorker(RayActor): wraps a WorkerProcess. Inherits lifecycle,
        adds execute(tree) for everybase tree dispatch.

Usage:
    # Service on a Ray node
    service = await runtime.create(RayActorSpec(
        inner_spec=InvisiblesServerSpec(...),
    ))

    # Worker on a Ray node
    worker = await runtime.create(RayWorkerSpec(
        inner_spec=WorkerSpec(context=ContextSpec(storage=nav_proxy)),
    ))
    ctx = ctx.bind(worker, Worker, 0)
"""

from __future__ import annotations

import asyncio

import attrs
import ray
from composables import Resource, ResourceSpec


__all__ = [
    "RayActor",
    "RayActorSpec",
    "RayWorker",
    "RayWorkerSpec",
]


# ============================================================================
# Resources
# ============================================================================


class RayActor(Resource):
    """Composables Resource hosting a Resource on a Ray node via RayProcess.

    On setup: creates a RayProcess actor, sends inner_spec.
    On cleanup: shuts down the remote actor.
    """

    spec: RayActorSpec

    async def setup(self) -> None:
        """Start a Ray actor and create the inner Resource remotely."""
        from .process import RayProcess

        self._process = self._create_process(RayProcess)
        await self._process.start.remote(self.spec.inner_spec)

        # If inner spec has an address (server), wait for background thread to bind
        if hasattr(self.spec.inner_spec, "address"):
            self._address = self.spec.inner_spec.address
            await asyncio.sleep(0.2)
        else:
            self._address = None

    @property
    def address(self) -> str | None:
        """Service address, if this actor runs an InvisiblesServer."""
        return self._address

    async def cleanup(self) -> None:
        """Shutdown the remote Ray actor."""
        if hasattr(self, "_process"):
            try:
                await self._process.shutdown.remote()
            except Exception:  # noqa: S110
                pass
            ray.kill(self._process)

    def _create_process(self, process_cls: type) -> object:
        """Create a Ray actor with optional node placement."""
        options: dict = {}
        if self.spec.node is not None:
            options["resources"] = {f"node:{self.spec.node}": 1}
        return process_cls.options(**options).remote()


class RayWorker(RayActor):
    """Composables Resource hosting a Worker on a Ray node via WorkerProcess.

    Inherits lifecycle from RayActor, adds execute() for tree dispatch.
    Bound to Context for Teleport: ctx[Worker, idx].execute(tree).
    """

    spec: RayWorkerSpec

    async def setup(self) -> None:
        """Start a WorkerProcess and create the Worker remotely."""
        from .process import WorkerProcess

        self._process = self._create_process(WorkerProcess)
        await self._process.start.remote(self.spec.inner_spec)
        self._address = None

    async def execute(self, tree: object) -> object:
        """Dispatch tree execution to the remote WorkerProcess.

        Called by Teleport via ctx[Worker, idx].execute(tree).

        Args:
            tree: An everybase Executable (tree node).

        Returns:
            Result of tree execution on the remote worker.
        """
        return await self._process.execute.remote(tree)


# ============================================================================
# Specs
# ============================================================================


@attrs.define(frozen=True, slots=True, kw_only=True)
class RayActorSpec(ResourceSpec):
    """Spec for RayActor (generic service on a Ray node).

    Attributes:
        inner_spec: The composables Spec to create inside the Ray actor.
        node: Optional Ray node name for placement (e.g. "red", "blue").
    """

    factory: type = RayActor
    name: str = "ray-actor"

    inner_spec: ResourceSpec = attrs.field()
    node: str | None = None


@attrs.define(frozen=True, slots=True, kw_only=True)
class RayWorkerSpec(ResourceSpec):
    """Spec for RayWorker (everybase worker on a Ray node).

    Attributes:
        inner_spec: A WorkerSpec with ContextSpec for storage setup.
        node: Optional Ray node name for placement (e.g. "red", "blue").
    """

    factory: type = RayWorker
    name: str = "ray-worker"

    inner_spec: ResourceSpec = attrs.field()
    node: str | None = None
