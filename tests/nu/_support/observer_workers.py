"""Helpers for the ``nu.kv`` observer-preset tests that have to survive a ``spawn``.

A child process is started by pickling a function by reference, so the entry
point and everything it names have to live in an importable module rather than
in the test file. The child here is a whole nu tree with
``nu.kv.proxy_observer`` at its head, which is the thing under test.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import nu
import nu.kv
from nu.core.reactive import ObserverProtocol


if TYPE_CHECKING:
    from nu.lang.runtime import Context


__all__ = ["Reactor", "Rebinder", "child_main", "unbind_child_main"]


class Reactor:
    """Subscribes on whatever observer is bound and reports every key it hears.

    A fabric rather than a term because subscribing wants the Context, and a
    bracket is where a worker's process-scope wiring belongs anyway.
    """

    def __init__(self, *, out: Any = None, prefix: tuple[str, ...] = ()) -> None:
        self.out = out
        self.prefix = prefix
        self._sub: Any = None

    async def asetup(self, ctx: Context) -> None:
        """Subscribe on the bound observer and say so."""
        from virtuals.tkv.filter import PrefixFilter
        from virtuals.tkv.observer import SubscriptionOptions

        observer = ctx.get(ObserverProtocol)
        self._sub = observer.subscribe(SubscriptionOptions(filter=PrefixFilter(prefix=self.prefix)))
        self._sub.bind(self._on_key)
        self.out.put(("ready", None))

    async def acleanup(self) -> None:
        """Close the subscription, which unbinds this receiver at the far end."""
        if self._sub is not None:
            self._sub.close()
            self._sub = None

    def _on_key(self, key: Any) -> None:
        self.out.put(("key", tuple(key)))


class Rebinder:
    """Binds two receivers, unbinds one, and reports whichever still fires.

    The far side of the socket is the whole point. ``unbind`` has to reach the
    subscription in the other process and pick out a receiver that process only
    ever saw as a remote handle, which is what ``React`` does every time its
    body restarts.
    """

    def __init__(self, *, out: Any = None, prefix: tuple[str, ...] = ()) -> None:
        self.out = out
        self.prefix = prefix
        self._sub: Any = None

    async def asetup(self, ctx: Context) -> None:
        """Bind both receivers, drop one, and say so."""
        from virtuals.tkv.filter import PrefixFilter
        from virtuals.tkv.observer import SubscriptionOptions

        def dropped(key: Any) -> None:
            self.out.put(("dropped", tuple(key)))

        def kept(key: Any) -> None:
            self.out.put(("kept", tuple(key)))

        observer = ctx.get(ObserverProtocol)
        self._sub = observer.subscribe(SubscriptionOptions(filter=PrefixFilter(prefix=self.prefix)))
        self._sub.bind(dropped)
        self._sub.bind(kept)
        self._sub.unbind(dropped)
        self._sub.unbind(dropped)  # twice, because a finally can run on a dead one
        self.out.put(("ready", None))

    async def acleanup(self) -> None:
        """Close the subscription this opened."""
        if self._sub is not None:
            self._sub.close()
            self._sub = None


def child_main(address: str, out: Any, prefix: tuple[str, ...]) -> None:
    """Run a tree that binds the parent's observer and listens until killed."""
    tree = nu.With(
        nu.kv.proxy_observer(address),
        nu.Provide(Reactor, {"out": out, "prefix": prefix}),
        body=nu.DelayedDo(60.0, nu.SetCmd(nu.AttrRef("idle"), 1)),
    )
    asyncio.run(nu.arun(tree, nu.Context()))


def unbind_child_main(address: str, out: Any, prefix: tuple[str, ...]) -> None:
    """Run a tree whose subscriber unbinds one of its two receivers."""
    tree = nu.With(
        nu.kv.proxy_observer(address),
        nu.Provide(Rebinder, {"out": out, "prefix": prefix}),
        body=nu.DelayedDo(60.0, nu.SetCmd(nu.AttrRef("idle"), 1)),
    )
    asyncio.run(nu.arun(tree, nu.Context()))
