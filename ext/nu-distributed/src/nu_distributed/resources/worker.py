"""Worker - executes everybase trees.

A Worker is a service with its own Context. It receives trees
and executes them. The Worker's Context determines topology -
it can have its own storage, proxy to a remote one, or share
with other workers.

Workers are bound to the root Context by index tags:
    ctx.bind(Worker, worker, 0)
    ctx.bind(Worker, worker, 1)

Teleport resolves workers from context:
    ctx[Worker, idx]
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import attrs

from composables import Attach, Resource, ResourceSpec

from .context import ContextSpec


if TYPE_CHECKING:
    from nu import Context


__all__ = [
    "Worker",
    "WorkerSpec",
]


class Worker(Resource):
    """Executes everybase trees against its own Context."""

    spec: WorkerSpec
    context = Attach()

    async def execute(self, tree: object) -> object:
        """Execute an everybase tree against this worker's Context."""
        return await tree.execute(self.context.ctx)

    @property
    def ctx(self) -> Context:
        """The worker's everybase Context."""
        return self.context.ctx


@attrs.define(frozen=True, slots=True, kw_only=True)
class WorkerSpec(ResourceSpec):
    """Spec for Worker."""

    factory: type = Worker
    name: str = "worker"

    context: ContextSpec = attrs.Factory(ContextSpec)
