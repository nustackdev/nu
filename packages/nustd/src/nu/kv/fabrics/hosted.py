"""The bound observer, wrapped for subscribers that are other processes.

Not a backend. ``InMemoryObserver`` and ``RedisObserver`` own a transport and
know how a change physically arrives; this owns neither and wraps whichever of
them is bound, adding the one thing a socket needs that a local call does not.

That thing is eviction. A receiver reached over a socket stops working when
its process dies, and a backend has no way to tell that from a callback with a
bug, so it keeps the dead one bound and fails on it forever. Here the real
subscription holds one local callback and the remote receivers hang off that,
so a receiver whose process is gone is dropped on its first failure and the
backend never sees a remote handle at all.

``nu.kv.served_observer`` is what puts this on a socket.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from nu.core.reactive import ObserverProtocol


if TYPE_CHECKING:
    from nu.lang.runtime import Context


__all__ = ["HostedObserver", "HostedSubscription"]


logger = logging.getLogger(__name__)


Receiver = Callable[[Any], None]


class HostedSubscription:
    """One subscription whose receivers may be in another process.

    Binds a single local callback on the real subscription and fans out from
    there. A receiver that raises is a process that died, so it gets dropped
    rather than propagated into the notify path.
    """

    def __init__(self, inner: Any, on_done: Callable[[HostedSubscription], None]) -> None:  # noqa: ANN401 -- any virtuals Subscription
        self._inner = inner
        self._on_done = on_done
        self._lock = threading.Lock()
        self._receivers: list[Receiver] = []
        self._bound = False
        self._closed = False
        inner.bind(self._fire)

    @property
    def receivers(self) -> tuple[Receiver, ...]:
        """Everything still bound. What a test counts corpses with."""
        with self._lock:
            return tuple(self._receivers)

    def bind(self, receiver: Receiver) -> None:
        """Register ``receiver`` to fire on every matching key."""
        with self._lock:
            if not self._closed:
                self._receivers.append(receiver)
                self._bound = True

    def close(self) -> None:
        """Close the real subscription and forget every receiver."""
        with self._lock:
            if self._closed:
                return
            self._closed = True
            self._receivers = []
        try:
            self._inner.close()
        except Exception:
            logger.debug("inner subscription close raised", exc_info=True)
        self._on_done(self)

    def _fire(self, key: Any) -> None:  # noqa: ANN401 -- the key shape is the backend's
        """Hand ``key`` to every receiver, dropping the ones that are gone.

        Runs on the observer's dispatch thread, so a raise here is a raise in
        the notify path of the process that owns the store. Compared by
        identity, because deciding whether two remote handles are equal is a
        round trip to a process that may be the one that just died.
        """
        with self._lock:
            receivers = tuple(self._receivers)
        dead = []
        for receiver in receivers:
            try:
                receiver(key)
            except Exception:  # one dead subscriber must not end the loop
                dead.append(receiver)
        if not dead:
            return
        logger.debug("dropping %d receiver(s) whose process is gone", len(dead))
        with self._lock:
            self._receivers = [r for r in self._receivers if not any(r is gone for gone in dead)]
            orphaned = self._bound and not self._receivers and not self._closed
        if orphaned:
            self.close()


class HostedObserver:
    """An ``ObserverProtocol`` whose subscribers may be other processes.

    Forwards to whichever observer this process bound and hands back a
    :class:`HostedSubscription`. ``options`` passes through unread, the way nu
    treats it everywhere.
    """

    def __init__(self, *, target_tag: object = None) -> None:
        self.target_tag = target_tag
        self._inner: Any = None
        self._lock = threading.Lock()
        self._open: list[HostedSubscription] = []

    def setup(self, ctx: Context) -> None:
        """Take the observer bound in this process."""
        tags = (self.target_tag,) if self.target_tag is not None else ()
        self._inner = ctx.get(ObserverProtocol, *tags)

    def cleanup(self) -> None:
        """Close every subscription this ever handed out."""
        with self._lock:
            open_subs, self._open = self._open, []
        for sub in open_subs:
            sub.close()
        self._inner = None

    async def asetup(self, ctx: Context) -> None:
        """Async shim: setup is sync work."""
        self.setup(ctx)

    async def acleanup(self) -> None:
        """Async shim: cleanup is sync work."""
        self.cleanup()

    def subscribe(self, options: Any) -> HostedSubscription:  # noqa: ANN401 -- backend-defined
        """Subscribe on the real observer, hand back a hosted handle."""
        sub = HostedSubscription(self._inner.subscribe(options), self._forget)
        with self._lock:
            self._open.append(sub)
        return sub

    def _forget(self, sub: HostedSubscription) -> None:
        with self._lock:
            self._open = [s for s in self._open if s is not sub]
