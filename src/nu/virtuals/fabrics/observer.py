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
        # Defer parent init until asetup - Codec comes from ctx.
        pass

    async def asetup(self, ctx: Context) -> None:
        codec = ctx.get(Codec)
        _InMemoryObserver.__init__(self, codec=codec)
        self.connect()

    async def acleanup(self) -> None:
        self.disconnect()


class RedisObserver:
    """Inter-process observer via Redis pub/sub. Lazy-loaded to avoid a hard
    ``redis`` dep.
    """

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
