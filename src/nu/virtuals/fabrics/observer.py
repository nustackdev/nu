"""Nu fabrics wrapping virtuals observers.

Observers receive change notifications from Storage writes. All observers are
``FabricLifecycle`` - ``asetup`` connects, ``acleanup`` disconnects.

DI convention: ``asetup`` reads its ``Codec`` from ctx. Provision a ``Codec``
in an outer ``Provide`` and the observer picks it up.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from virtuals._backends.observers.mem import InMemoryObserver as _InMemoryObserver

from .codec import Codec


if TYPE_CHECKING:
    from nu.lang.runtime import Context


__all__ = ["InMemoryObserver", "RedisObserver"]


class InMemoryObserver(_InMemoryObserver):
    """In-process, thread-safe observer. Reads ``Codec`` from ctx during setup."""

    def __init__(self) -> None:
        # Defer parent init until setup - Codec comes from ctx.
        pass

    def setup(self, ctx: Context) -> None:
        """Read Codec from ctx, init the parent, and connect."""
        codec = ctx.get(Codec)
        _InMemoryObserver.__init__(self, codec=codec)
        self.connect()

    def cleanup(self) -> None:
        """Disconnect the observer."""
        self.disconnect()

    async def asetup(self, ctx: Context) -> None:
        """Async shim: setup is sync work."""
        self.setup(ctx)

    async def acleanup(self) -> None:
        """Async shim: cleanup is sync work."""
        self.cleanup()


class RedisObserver:
    """Inter-process observer via Redis pub/sub; lazy-loaded to skip the hard dep.

    ``_nu_async_only = True`` because a Redis connect + pub/sub subscribe is
    real network IO that we don't want blocking a sync runtime. Use
    ``nu.arun`` for any tree that includes this observer.
    """

    _nu_async_only = True

    def __init__(
        self,
        *,
        redis_url: str = "redis://localhost:6379",
        channel_prefix: str = "everyshape",
        notify_self: bool = True,
    ) -> None:
        self.redis_url = redis_url
        self.channel_prefix = channel_prefix
        self.notify_self = notify_self
        self._backing = None

    async def asetup(self, ctx: Context) -> None:
        from virtuals._backends.observers.redis_pubsub import RedisObserver as _RedisObserver

        codec = ctx.get(Codec)
        self._backing = _RedisObserver(
            codec=codec,
            redis_url=self.redis_url,
            channel_prefix=self.channel_prefix,
            notify_self=self.notify_self,
        )
        self._backing.connect()

    async def acleanup(self) -> None:
        if self._backing is not None:
            self._backing.disconnect()
            self._backing = None

    def __getattr__(self, name: str) -> object:
        # Delegate any observer-protocol access to the backing instance.
        if name.startswith("_"):
            raise AttributeError(name)
        if self._backing is None:
            msg = "RedisObserver used before asetup"
            raise RuntimeError(msg)
        return getattr(self._backing, name)
