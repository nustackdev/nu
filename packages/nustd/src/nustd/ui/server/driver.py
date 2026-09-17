"""The Nu side of a connection: relay it in, fold over it, hand it its session.

Four terms, in the order they run:

- ``seed_sessions`` -- create the registry collection before anyone watches it.
- ``session_driver`` -- turn the server's connect / disconnect moments into
  rows appearing and disappearing.
- ``sessions_fold`` -- one live arm per row.
- ``session_for`` -- inside an arm, bind that connection's transport.

The driver is Nu rather than a couple of lines in the ws endpoint because the
endpoint has no Nu runtime around it. Writing kv from there would mean either
calling the navigator directly, going behind the tree's back, or spinning up a
nested runtime, which is the thing this refactor exists to delete. So the
endpoint announces and Nu writes.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import nu
import nustd.kv
from nu.core.spans.bracket import _LifecycleBracket
from nustd.ui.core.session import Session

from .fabric import WebServer
from .refs import CONNECT_ATTR, DISCONNECT_ATTR, SID_ATTR, ServerRef, Sessions, WsSessions


if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from nu.lang import Nu
    from nu.lang.runtime import Context


__all__ = [
    "SessionFor",
    "seed_sessions",
    "session_driver",
    "session_for",
    "sessions_fold",
]


def seed_sessions(*, scope: type[nu.Shape] = Sessions) -> Nu:
    """Bring the registry collection into being. Runs before anything watches it.

    A subscription over a container that is not there resolves to INVALID and
    then never fires again -- no error, just a fold that never sees its first
    connection. So this lands ahead of the fold, not beside it.

    Args:
        scope: the registry shape, as the tag its storage resolves under.

    Notes:
        - ``nu.Dict.create()`` and never a plain ``{}``. A literal is captured
          once when the Form is built and would be shared by every evaluation.
    """
    return nustd.kv.auto_flow_atomic(WsSessions.init(nu.Dict.create()), scope=scope)


def session_driver(*, scope: type[nu.Shape] = Sessions) -> Nu:
    """Relay the server's connect / disconnect moments into the registry.

    Two arms, forever. A connection writes its row; a disconnection deletes
    it. That is the entire state: the key's presence is what the fold reads,
    so there is no flag on either side to set. There could not be one --
    writing into the collection being watched is the feedback loop the
    reactive atoms warn about.

    Args:
        scope: the registry shape, as the tag its storage resolves under.

    Notes:
        - ``changed_key`` parks the fired value on ``ctx.attrs`` before each
          body run, which is how the sid reaches the write. Two names because
          ``ParallelAsync`` shares one attrs space across its arms.
    """
    connected = nu.StrAttrRef(CONNECT_ATTR)
    gone = nu.StrAttrRef(DISCONNECT_ATTR)
    return nu.ParallelAsync(
        nu.ReactForever(
            ServerRef().on_connect(),
            nustd.kv.auto_flow_atomic(
                WsSessions[connected].sid.set(connected),
                scope=scope,
            ),
            changed_key=CONNECT_ATTR,
        ),
        nu.ReactForever(
            ServerRef().on_disconnect(),
            nustd.kv.auto_flow_atomic(WsSessions.del_item(gone), scope=scope),
            changed_key=DISCONNECT_ATTR,
        ),
    )


def sessions_fold(arm: Nu, *, scope: type[nu.Shape] = Sessions) -> Nu:
    """Run ``arm`` once per live connection, births and deaths included.

    Args:
        arm: the body one connection gets. Spawned when its row appears,
            cancelled and drained when the row goes.
        scope: the registry shape, as the tag its storage resolves under.

    Notes:
        - ``nu.list`` around the keys, not the lazy view. The fold is a Flow,
          so the atomicity pass brackets each of its slots separately and the
          items slot's snapshot closes the moment that thunk returns -- a lazy
          view handed out of it dies on first read with a closed-context
          error.
        - ``on_children_change`` and not ``on_change``. The children filter is
          length exact; the generic one is an unbounded prefix. With the
          latter, writing anything inside one session's row would look like
          the collection changing and restart that tab's whole app.
        - Each sessions term is pre-wrapped at ``scope``. An untagged pass
          over a tree holding these would claim them (an unscoped pass
          dominates everything) and insert an untagged bracket, which the
          tagged lookup then misses -- falling back to the app's store, which
          has no sessions in it.
    """
    ids = nustd.kv.auto_flow_atomic(nu.list(WsSessions.keys()), scope=scope)
    changed = nustd.kv.auto_flow_atomic(WsSessions.on_children_change(), scope=scope)
    return nu.ForEachParReactive(ids, changed, arm, SID_ATTR)


class SessionFor(_LifecycleBracket):
    """Bind the ws transport of the connection this arm belongs to.

    Reads the sid off the Context the fold branched for this arm, looks the
    live session up in the server's connection book, and binds it under the
    abstract ``Session`` so every Ref underneath resolves through it.

    Not a ``Provide``: what gets bound is an object the server already holds,
    not one this bracket constructs. And the sid cannot be a child term --
    a bracket's lifecycle runs with a Context, not a Runtime, so there is
    nothing to evaluate a term against. It arrives through attrs instead,
    which is the same slot a loop variable would have been read from.

    Nothing is torn down. The server owns the session and the endpoint closes
    it; hanging up on a browser because one arm of its page ended would be
    exactly the inversion this refactor removes.

    Args:
        body: the tree that runs with the session bound.
        sid_attr: the attr the fold parked this arm's session id under.
    """

    def __init__(self, body: Nu | None = None, *, sid_attr: str = SID_ATTR) -> None:
        super().__init__(body)
        self._payload["sid_attr"] = sid_attr

    @asynccontextmanager
    async def _aopen(self, ctx: Context) -> AsyncIterator[Context]:
        attr = self._payload["sid_attr"]
        sid = ctx.attrs.get(attr)
        if sid is None:
            msg = f"SessionFor found no {attr!r} on the Context; it runs inside the fold"
            raise LookupError(msg)
        session = ctx.get(WebServer).session(sid)
        if session is None:
            # Reachable, and transiently so: the browser can go away between
            # the connect and the fold's next pass. The arm raises, the fold
            # isolates it, the row delete lands on the following pass and the
            # key goes. One wasted spawn, no leak.
            msg = f"no live ws session for {sid!r}"
            raise LookupError(msg)
        yield ctx.bind(Session, session)


def session_for(sid_attr: str = SID_ATTR, body: Nu | None = None) -> SessionFor:
    """``SessionFor`` in call order: the attr first, then what runs under it.

    Example:
        >>> session_for(SID_ATTR, App.boot() >> program)
    """
    return SessionFor(body, sid_attr=sid_attr)
