"""The kv stack the sessions registry lives in, tagged to its own shape.

The registry is kv, so it needs a storage and a navigator. What it must not
do is bring a whole second kv stack with it. Every reactive atom resolves its
observer *untagged*, and binding a fabric overwrites the entry for its
``(type, tags)`` pair -- so a second full navigator preset inside a program
that already has one would replace the app's observer and the app would go
silently deaf, still writing, never reacting.

So: bind a tagged ``InMemoryStorage`` and ``Navigator``, and inherit Codec,
transport, publisher and observer from whatever kv stack is already in the
tree. When there is no kv stack at all -- the one-file example with no
navigator anywhere -- stand up the untagged half so the registry has
something to publish onto.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import nu
from nu.core.reactive import ObserverProtocol
from nu.core.spans.bracket import _LifecycleBracket
from nustd.kv.fabrics import (
    Codec,
    InMemoryObserver,
    InMemoryPublisher,
    InMemoryStorage,
    InMemoryTransport,
    Navigator,
    noop_kwargs,
)

from .refs import Sessions


if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from nu.lang.runtime import Context


__all__ = ["sessions_store"]


class _NotifyIfMissing(_LifecycleBracket):
    """Stand up the untagged half of a kv stack, but only if there is none.

    One gate, ``ctx.has(Codec)``, and that is deliberate. Every kv preset
    binds ``Codec`` untagged and binds it first, so it is exactly the question
    "is there a kv stack here". Gating each of the four fabrics separately
    would half-fill under a redis stack: a ``RedisObserver`` is bound, so the
    observer gate passes, and the sessions storage would end up publishing
    onto a fresh in-process transport nobody is listening to -- deaf again,
    and silently. One gate cannot do that.

    Everything it opens it closes, LIFO. ``Codec`` is bound but never set up
    or torn down; it has no lifecycle, its constructor does all the work.
    """

    @asynccontextmanager
    async def _aopen(self, ctx: Context) -> AsyncIterator[Context]:
        if ctx.has(Codec):
            yield ctx
            return
        opened: list = []
        try:
            ctx = ctx.bind(Codec, Codec(**noop_kwargs()))
            transport = InMemoryTransport()
            await transport.asetup(ctx)
            opened.append(transport)
            ctx = ctx.bind(InMemoryTransport, transport)
            publisher = InMemoryPublisher()
            await publisher.asetup(ctx)
            opened.append(publisher)
            ctx = ctx.bind(InMemoryPublisher, publisher)
            observer = InMemoryObserver()
            await observer.asetup(ctx)
            opened.append(observer)
            # Bound under the protocol explicitly: `_nu_bind_as` is honoured by
            # `Provide`, not by a hand-rolled bracket, and the reactive atoms
            # all do a bare `ctx.get(ObserverProtocol)`.
            ctx = ctx.bind(ObserverProtocol, observer)
            yield ctx
        finally:
            for fabric in reversed(opened):
                await fabric.acleanup()


def sessions_store(
    *,
    scope: type[nu.Shape] = Sessions,
    publisher_type: type = InMemoryPublisher,
) -> nu.With:
    """The storage and navigator the sessions registry resolves through.

    Tagged to the sessions shape, so it sits alongside the app's own store
    rather than on top of it: a Ref carries its root shape as the tag it
    resolves a Navigator under, and these two bind under that same tag.

    Args:
        scope: the shape whose refs this store answers, and the tag it binds
            under. Only worth passing if the registry shape is subclassed.
        publisher_type: the publisher the registry's storage routes writes
            through. The default covers every non-redis preset, all of which
            bind ``InMemoryPublisher`` untagged. Under a redis stack pass
            ``RedisPublisher`` -- the registry's writes have to reach the same
            observer the fold subscribes on.

    Notes:
        - Deliberately partial. Codec, transport, publisher and observer are
          inherited from the surrounding kv stack, because a second untagged
          binding of any of them would take the app's place and leave the
          app's own reactions dead.
        - With no kv stack in the tree at all, the untagged half is stood up
          here and torn down with it.

    Example:
        >>> nu.With(nustd.ui.sessions_store(), body=program)
    """
    return nu.With(
        _NotifyIfMissing(),
        nu.Provide(InMemoryStorage, {"publisher_type": publisher_type}, tags=(scope,)),
        nu.Provide(
            Navigator,
            {"storage_type": InMemoryStorage, "storage_tags": (scope,)},
            tags=(scope,),
        ),
    )
