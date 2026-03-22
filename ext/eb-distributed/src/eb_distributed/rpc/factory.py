"""ResourceFactory - composables Resource for creating and managing Resources.

Server-side factory exposed as the root service of an InvisiblesServer.
Clients call get_resource(spec) directly - specs are registered as value
types in invisibles, so they fly through RPC by value automatically.
"""

from __future__ import annotations

import asyncio
from logging import getLogger
from typing import Any

import attrs
from composables import Resource, ResourceSpec


__all__ = [
    "ResourceFactory",
    "ResourceFactorySpec",
]

logger = getLogger(__name__)


class ResourceFactory(Resource):
    """Composables Resource that creates other Resources on demand via RPC.

    Holds a reference to its Runtime and event loop. Clients call
    get_resource(spec) through RPC. Specs are registered as value types
    in invisibles so they serialize by value automatically (no manual
    pickle.dumps needed). Resources are deduplicated by spec key.
    """

    spec: ResourceFactorySpec

    async def setup(self) -> None:
        """Capture the event loop for sync->async bridging."""
        self._loop = asyncio.get_running_loop()
        self._resources: dict[str, Any] = {}

    def get_resource(self, spec: ResourceSpec) -> object:
        """Get or create a resource from spec.

        Called by clients through RPC. Specs arrive by value (registered
        as value types in invisibles). Creates the resource via Runtime
        if not cached, returns it. Invisibles transparently proxies the
        return value.

        Args:
            spec: ResourceSpec for the resource to create/retrieve

        Returns:
            Resource instance (proxied by invisibles on the client side)
        """
        key = spec.key

        if key in self._resources:
            logger.debug(f"Returning cached resource: {spec.name}")
            return self._resources[key]

        logger.info(f"Creating resource: {spec.name}")
        future = asyncio.run_coroutine_threadsafe(self._runtime.create(spec), self._loop)
        resource = future.result(timeout=30.0)
        self._resources[key] = resource
        logger.info(f"Resource created: {spec.name}")
        return resource

    def get_resource_count(self) -> int:
        """Return number of managed resources."""
        return len(self._resources)

    def ping(self) -> str:
        """Health check."""
        return "pong"


@attrs.define(frozen=True, slots=True, kw_only=True)
class ResourceFactorySpec(ResourceSpec):
    """Spec for ResourceFactory."""

    factory: type = ResourceFactory
    name: str = "resource-factory"
