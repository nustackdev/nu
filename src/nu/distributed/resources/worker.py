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

    async def aexecute(self, tree: object, *, attrs: dict | None = None) -> object:
        """Execute a Nu tree against this worker's Context.

        ``attrs`` (optional) is merged into the worker context's attrs
        before execution (used by ``Teleport(carry=True)``).

        Returns the last yielded value, or None if the tree yielded nothing.
        """
        from nu import acollect
        from nu.lang import compile as compile_term

        ctx = self.context.ctx
        if attrs:
            ctx = ctx._copy()
            for key, value in attrs.items():
                ctx.attrs[key] = value
        program = compile_term(tree)
        values, _ = await acollect(program, ctx)
        return values[-1] if values else None

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
