"""Nu fabrics wrapping virtuals *read-side* observers.

Observers subscribe local callbacks against filters, listen on a shared
transport for inbound keys, match against a per-process
``SubscriptionRegistry``, and fan out to bound callbacks. They live at
process scope and know nothing about local writes.

All observer fabrics bind their instance under ``ObserverProtocol`` via
``_nu_bind_as`` so ``nu.core.reactive`` queries can find "the observer"
without knowing which backend is active.

Observer backends:

- ``InMemoryObserver`` -- takes an ``InMemoryTransport`` from ctx and
  registers a listener on it.
- ``RedisObserver`` -- async-only. Owns the registry HASH mutations,
  cluster control-channel PUBLISH, cleanup sweep, and pubsub listener.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from virtuals._backends.observers.mem import InMemoryObserver as _InMemoryObserver
from virtuals.tkv.observer import ObserverProtocol

from .transport import InMemoryTransport


if TYPE_CHECKING:
    from nu.lang.runtime import Context


__all__ = ["InMemoryObserver", "RedisObserver"]


class InMemoryObserver(_InMemoryObserver):
    """In-process observer. Reads the shared ``InMemoryTransport`` from ctx.

    Binds under ``ObserverProtocol`` so ``nu.core.reactive`` queries can
    resolve "the observer" without knowing the backend.
    """

    _nu_bind_as = ObserverProtocol

    def __init__(self) -> None:
        # Defer parent init until setup - InMemoryTransport comes from ctx.
        pass

    def setup(self, ctx: Context) -> None:
        """Read the transport from ctx, init the parent, connect."""
        transport = ctx.get(InMemoryTransport)
        _InMemoryObserver.__init__(self, transport=transport)
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
    """Inter-process observer via Redis pub/sub. Lazy-imports ``redis``.

    ``_nu_async_only = True`` because a Redis connect + pub/sub subscribe
    is real network IO we don't want blocking a sync runtime. Use
    ``nu.arun`` for any tree that includes this observer.

    Binds under ``ObserverProtocol`` so ``nu.core.reactive`` queries can
    resolve "the observer" without knowing the backend.
    """

    _nu_async_only = True
    _nu_bind_as = ObserverProtocol

    def __init__(
        self,
        *,
        redis_url: str = "redis://localhost:6379",
        channel_prefix: str = "nu",
    ) -> None:
        self.redis_url = redis_url
        self.channel_prefix = channel_prefix
        self._backing: object | None = None

    async def asetup(self, ctx: Context) -> None:
        """Lazy-import the backing class, construct, connect."""
        del ctx
        from virtuals._backends.observers.redis_pubsub import RedisObserver as _RedisObserver

        self._backing = _RedisObserver(
            redis_url=self.redis_url,
            channel_prefix=self.channel_prefix,
        )
        self._backing.connect()

    async def acleanup(self) -> None:
        """Disconnect the backing observer and drop the reference."""
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
