"""ContextResource - composables Resource that builds an everybase Context.

Attaches a NavigatorResource and binds its storage to the Context.

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
    """Builds an everybase Context with attached storage bound."""

    spec: ContextSpec
    storage = Attach()

    async def setup(self) -> None:
        """Build Context and bind the navigator's underlying storage."""
        from virtuals.tkv.storage import StorageProtocol

        self._ctx = Context()
        # .storage property returns the underlying storage from the navigator
        # Works both locally (NavigatorResource.storage) and via proxy (RPC)
        self._ctx = self._ctx.bind(self.storage.storage, StorageProtocol)

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
