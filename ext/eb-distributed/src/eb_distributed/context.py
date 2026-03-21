"""ContextResource - composables Resource that builds an everybase Context.

Attaches a NavigatorResource and binds it as Navigator to the Context.

Usage:
    spec = ContextSpec(
        storage=NavigatorSpec(
            storage_resource=InMemoryStorageSpec()
        )
    )

    async with Runtime() as runtime:
        ctx_resource = await runtime.create(spec)
        await some_flow.execute(ctx_resource.ctx)
"""

from __future__ import annotations

import attrs
from composables import Attach, Resource, ResourceSpec

from everybase import Context

from .storage import NavigatorSpec


__all__ = [
    "ContextResource",
    "ContextSpec",
]


class ContextResource(Resource):
    """Builds an everybase Context with attached Navigator bound."""

    spec: ContextSpec
    storage = Attach()

    async def setup(self) -> None:
        """Build Context and bind the Navigator."""
        from virtuals import Navigator

        self._ctx = Context()
        # Bind the navigator itself - spans look up Navigator from context
        self._ctx = self._ctx.bind(self.storage, Navigator)

    @property
    def ctx(self) -> Context:
        """The everybase Context, ready for flow execution."""
        return self._ctx


@attrs.define(frozen=True, slots=True, kw_only=True)
class ContextSpec(ResourceSpec):
    """Spec for ContextResource."""

    factory: type = ContextResource
    name: str = "context"

    storage: NavigatorSpec = attrs.Factory(NavigatorSpec)
