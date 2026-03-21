"""ResourceFactory - composables Resource for creating and managing Resources.

Server-side factory exposed as the root service of an InvisiblesServer.
Clients call get_resource(spec_data) with pre-serialized spec bytes.
The factory deserializes, creates the resource via Runtime, and returns it.
"""

from __future__ import annotations

import asyncio
import pickle  # nosec: S301
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
    get_resource(spec_data) through RPC with pickle-serialized spec bytes.
    Specs are serialized on the client side to avoid RPC round trips
    for attribute access (specs are frozen data, no lifecycle).
    Resources are deduplicated by spec key.
    """

    spec: ResourceFactorySpec

    async def setup(self) -> None:
        """Capture the event loop for sync->async bridging."""
        self._loop = asyncio.get_running_loop()
        self._resources: dict[str, Any] = {}

    def get_resource(self, spec_data: bytes) -> object:
        """Get or create a resource from serialized spec.

        Called by clients through RPC. Deserializes the spec,
        creates the resource via Runtime if not cached, returns it.
        Invisibles transparently proxies the return value.

        Args:
            spec_data: pickle-serialized ResourceSpec

        Returns:
            Resource instance (proxied by invisibles on the client side)
        """
        spec: ResourceSpec = pickle.loads(spec_data)  # noqa: S301
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
