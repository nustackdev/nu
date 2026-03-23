"""Ray Resources - lifecycle wrappers for Ray processes.

RayActor: wraps a RayProcess. Manages lifecycle (setup/cleanup).
    Used for services (Navigator + InvisiblesServer, etc).

RayWorker(RayActor): wraps a WorkerProcess. Inherits lifecycle,
    adds execute(tree) for everybase tree dispatch.
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
    """Hosts a Resource on a Ray node via RayProcess.

    On setup: creates a RayProcess actor, sends inner_spec.
    On cleanup: shuts down the remote actor gracefully.
    """

    spec: RayActorSpec

    async def setup(self) -> None:
        """Start a Ray actor and create the inner Resource remotely."""
        from ..launcher.process import RayProcess

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
        """Shutdown the remote Ray actor gracefully."""
        if hasattr(self, "_process"):
            try:
                await self._process.shutdown.remote()
            except Exception:  # noqa: S110
                pass
            try:
                ray.kill(self._process)
            except Exception:  # noqa: S110
                pass

    def _create_process(self, process_cls: type) -> object:
        """Create a Ray actor with configured options."""
        options = self._build_ray_options()
        return process_cls.options(**options).remote()

    def _build_ray_options(self) -> dict:
        """Build Ray actor options from spec."""
        options: dict = {}

        if self.spec.node is not None:
            options["resources"] = {f"node:{self.spec.node}": 1}
        if self.spec.actor_name is not None:
            options["name"] = self.spec.actor_name
        if self.spec.num_cpus is not None:
            options["num_cpus"] = self.spec.num_cpus
        if self.spec.num_gpus is not None:
            options["num_gpus"] = self.spec.num_gpus
        if self.spec.max_restarts != 0:
            options["max_restarts"] = self.spec.max_restarts
        if self.spec.lifetime is not None:
            options["lifetime"] = self.spec.lifetime

        return options


class RayWorker(RayActor):
    """Hosts a Worker on a Ray node via WorkerProcess.

    Inherits lifecycle from RayActor, adds execute() for tree dispatch.
    Bound to Context for Teleport: ctx[Worker, idx].execute(tree).
    """

    spec: RayWorkerSpec

    async def setup(self) -> None:
        """Start a WorkerProcess and create the Worker remotely."""
        from ..launcher.process import WorkerProcess

        self._process = self._create_process(WorkerProcess)
        await self._process.start.remote(self.spec.inner_spec)
        self._address = None

    async def execute(self, tree: object) -> object:
        """Dispatch tree execution to the remote WorkerProcess."""
        return await self._process.execute.remote(tree)


# ============================================================================
# Specs
# ============================================================================


@attrs.define(frozen=True, slots=True, kw_only=True)
class _RaySpecBase(ResourceSpec):
    """Shared Ray actor configuration."""

    inner_spec: ResourceSpec = attrs.field()
    node: str | None = None
    actor_name: str | None = None
    num_cpus: float | None = None
    num_gpus: float | None = None
    max_restarts: int = 0
    lifetime: str | None = None
    tags: tuple = ()


@attrs.define(frozen=True, slots=True, kw_only=True)
class RayActorSpec(_RaySpecBase):
    """Spec for RayActor (generic service on a Ray node)."""

    factory: type = RayActor
    name: str = "ray-actor"


@attrs.define(frozen=True, slots=True, kw_only=True)
class RayWorkerSpec(_RaySpecBase):
    """Spec for RayWorker (everybase worker on a Ray node)."""

    factory: type = RayWorker
    name: str = "ray-worker"
