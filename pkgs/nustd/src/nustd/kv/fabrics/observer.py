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
- ``RedisObserver`` -- async-only. Owns the pubsub listener and registers
  each filter in valkey's server-side notify router once the subscribe is
  confirmed, so a subscription is live when ``subscribe`` returns. On
  reconnect it registers every filter again and sends each subscription one
  resync wake, so subscribers re-read what changed while it was down.

virtuals sends that wake as ``None`` in place of a key. Both observers hand
out subscriptions that turn it into nu's ``RESYNC`` marker, which level flows
re-read on and event flows skip. A kv key is a tuple, never ``None``, so the
mapping cannot catch a real change.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

from nu.core.reactive import RESYNC, ObserverProtocol
from virtuals._backends.observers.mem import InMemoryObserver as _InMemoryObserver

from .transport import InMemoryTransport


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Context


__all__ = ["InMemoryObserver", "RedisObserver", "ResyncSubscription"]


class ResyncSubscription:
    """A virtuals subscription whose ``None`` resync wake reaches nu as ``RESYNC``.

    Each bound receiver gets a wrapper; ``unbind`` finds it again by the
    receiver's identity, the way every subscription in nu compares receivers.
    Anything else (``filter_hash`` and the like) reads through to the inner one.
    """

    def __init__(self, inner: Any) -> None:  # noqa: ANN401 -- any virtuals Subscription
        self._inner = inner
        self._lock = threading.Lock()
        self._wrapped: list[tuple[Callable[[Any], None], Callable[[Any], None]]] = []

    def bind(self, receiver: Callable[[Any], None]) -> None:
        """Bind ``receiver``; a ``None`` wake reaches it as ``RESYNC``."""

        def translated(key: Any) -> None:  # noqa: ANN401 -- the backend's key shape
            receiver(RESYNC if key is None else key)

        with self._lock:
            self._wrapped.append((receiver, translated))
        self._inner.bind(translated)

    def unbind(self, receiver: Callable[[Any], None]) -> None:
        """Stop firing ``receiver``. A no-op when it is not bound."""
        with self._lock:
            gone = [w for r, w in self._wrapped if r is receiver]
            self._wrapped = [(r, w) for r, w in self._wrapped if r is not receiver]
        for w in gone:
            self._inner.unbind(w)

    def close(self) -> None:
        """Close the inner subscription and forget every receiver."""
        with self._lock:
            self._wrapped = []
        self._inner.close()

    def __getattr__(self, name: str) -> object:
        if name.startswith("_"):
            raise AttributeError(name)
        return getattr(self._inner, name)


class InMemoryObserver(_InMemoryObserver):
    """In-process observer. Reads the shared ``InMemoryTransport`` from ctx.

    Binds under ``ObserverProtocol`` so ``nu.core.reactive`` queries can
    resolve "the observer" without knowing the backend. ``transport_tags``
    names the tags its stack's transport is bound under.
    """

    _nu_bind_as = ObserverProtocol

    def __init__(self, *, transport_tags: tuple[object, ...] = ()) -> None:
        # Defer parent init until setup - InMemoryTransport comes from ctx.
        self._transport_tags = tuple(transport_tags)

    def setup(self, ctx: Context) -> None:
        """Read the transport from ctx, init the parent, connect."""
        transport = ctx.fabrics.get(InMemoryTransport, *self._transport_tags)
        _InMemoryObserver.__init__(self, transport=transport)
        self.connect()

    def subscribe(self, options: Any) -> ResyncSubscription:  # noqa: ANN401 -- backend-defined
        """Subscribe, with the resync wake carried as ``RESYNC``."""
        return ResyncSubscription(_InMemoryObserver.subscribe(self, options))

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

    def subscribe(self, options: Any) -> ResyncSubscription:  # noqa: ANN401 -- backend-defined
        """Subscribe, with the resync wake carried as ``RESYNC``."""
        backing: Any = self._backing
        if backing is None:
            msg = "RedisObserver used before asetup"
            raise RuntimeError(msg)
        return ResyncSubscription(backing.subscribe(options))

    def __getattr__(self, name: str) -> object:
        # Delegate any observer-protocol access to the backing instance.
        if name.startswith("_"):
            raise AttributeError(name)
        if self._backing is None:
            msg = "RedisObserver used before asetup"
            raise RuntimeError(msg)
        return getattr(self._backing, name)
