"""Nu fabrics wrapping virtuals *write-side* publishers.

Publishers are attached to a storage. On every storage write, storage
hands the modified keys to ``publisher.notify(keys)``. The publisher owns
routing onto the transport (in-mem bus or Redis pubsub); it knows nothing
about local subscriptions.

Publisher backends:

- ``InMemoryPublisher`` -- takes an ``InMemoryTransport`` from ctx and
  publishes onto it.
- ``RedisPublisher`` -- async-only. Owns the publish pipeline, control-
  channel listener, and cluster-wide interest cache.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from virtuals._backends.publishers.mem import InMemoryPublisher as _InMemoryPublisher

from .transport import InMemoryTransport


if TYPE_CHECKING:
    from nu.lang.runtime import Context


__all__ = ["InMemoryPublisher", "RedisPublisher"]


class InMemoryPublisher(_InMemoryPublisher):
    """In-process publisher. Reads the shared ``InMemoryTransport`` from ctx."""

    def __init__(self) -> None:
        # Defer parent init until setup - InMemoryTransport comes from ctx.
        pass

    def setup(self, ctx: Context) -> None:
        """Read the transport from ctx, init the parent, connect."""
        transport = ctx.get(InMemoryTransport)
        _InMemoryPublisher.__init__(self, transport=transport)
        self.connect()

    def cleanup(self) -> None:
        """Disconnect the publisher."""
        self.disconnect()

    async def asetup(self, ctx: Context) -> None:
        """Async shim: setup is sync work."""
        self.setup(ctx)

    async def acleanup(self) -> None:
        """Async shim: cleanup is sync work."""
        self.cleanup()


class RedisPublisher:
    """Inter-process publisher via Redis pub/sub. Lazy-imports ``redis``.

    ``_nu_async_only = True`` because a Redis connect + pub/sub subscribe
    is real network IO we don't want blocking a sync runtime. Use
    ``nu.arun`` for any tree that includes this publisher.
    """

    _nu_async_only = True

    def __init__(
        self,
        *,
        redis_url: str = "redis://localhost:6379",
        channel_prefix: str = "everyshape",
    ) -> None:
        self.redis_url = redis_url
        self.channel_prefix = channel_prefix
        self._backing: object | None = None

    async def asetup(self, ctx: Context) -> None:
        """Lazy-import the backing class, construct, connect."""
        del ctx
        from virtuals._backends.publishers.redis_pubsub import RedisPublisher as _RedisPublisher

        self._backing = _RedisPublisher(
            redis_url=self.redis_url,
            channel_prefix=self.channel_prefix,
        )
        self._backing.connect()

    async def acleanup(self) -> None:
        """Disconnect the backing publisher and drop the reference."""
        if self._backing is not None:
            self._backing.disconnect()
            self._backing = None

    def __getattr__(self, name: str) -> object:
        # Delegate any publisher-protocol access to the backing instance.
        if name.startswith("_"):
            raise AttributeError(name)
        if self._backing is None:
            msg = "RedisPublisher used before asetup"
            raise RuntimeError(msg)
        return getattr(self._backing, name)
