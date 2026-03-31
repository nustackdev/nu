"""Observer Resources - composables wrappers for virtuals observers.

Two observers:
- InMemoryObserver: in-process, thread-safe, O(key_length) pattern matching
- RedisObserver: inter-process via Redis pub/sub, automatic reconnection

Uses multiple inheritance: Resource IS the wrapped object.
RedisObserver is lazy-loaded to avoid hard dependency on redis package.
"""

from __future__ import annotations

import attrs
from composables import Attach, Resource, ResourceSpec
from virtuals._backends.observers.mem import InMemoryObserver

from .codec import CodecSpec, noop_codec_spec


__all__ = [
    "InMemoryObserverResource",
    "InMemoryObserverSpec",
    "RedisObserverResource",
    "RedisObserverSpec",
]


# ============================================================================
# InMemory Observer
# ============================================================================


class InMemoryObserverResource(Resource, InMemoryObserver):
    """Resource that IS an InMemoryObserver."""

    spec: InMemoryObserverSpec
    codec_resource = Attach()

    def __init__(self, spec: object = None, /) -> None:
        Resource.__init__(self, spec)

    async def setup(self) -> None:
        """Init observer with attached codec and connect."""
        InMemoryObserver.__init__(self, codec=self.codec_resource)
        self.connect()

    async def cleanup(self) -> None:
        """Disconnect observer."""
        self.disconnect()


@attrs.define(frozen=True, slots=True, kw_only=True)
class InMemoryObserverSpec(ResourceSpec):
    """Spec for InMemoryObserverResource."""

    factory: type = InMemoryObserverResource
    name: str = "observer"

    codec_resource: CodecSpec = attrs.Factory(noop_codec_spec)


# ============================================================================
# Redis Observer
# ============================================================================


class RedisObserverResource(Resource):
    """Resource that IS a RedisObserver. Inter-process via Redis pub/sub.

    Requires redis package: pip install redis
    """

    spec: RedisObserverSpec
    codec_resource = Attach()

    def __init__(self, spec: object = None, /) -> None:
        Resource.__init__(self, spec)

    async def setup(self) -> None:
        """Init Redis observer with attached codec and connect."""
        from virtuals._backends.observers.redis_pubsub import RedisObserver

        # Dynamically add RedisObserver as base class for IS-A relationship
        if RedisObserver not in type(self).__bases__:
            type(self).__bases__ = (Resource, RedisObserver)

        RedisObserver.__init__(
            self,
            codec=self.codec_resource,
            redis_url=self.spec.redis_url,
            channel_prefix=self.spec.channel_prefix,
            notify_self=self.spec.notify_self,
        )
        self.connect()

    async def cleanup(self) -> None:
        """Disconnect observer."""
        self.disconnect()


@attrs.define(frozen=True, slots=True, kw_only=True)
class RedisObserverSpec(ResourceSpec):
    """Spec for RedisObserverResource."""

    factory: type = RedisObserverResource
    name: str = "redis-observer"

    redis_url: str = "redis://localhost:6379"
    channel_prefix: str = "everyshape"
    notify_self: bool = True
    codec_resource: CodecSpec = attrs.Factory(noop_codec_spec)
