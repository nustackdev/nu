"""The Nu side of a connection: fold over the live ones, hand each its session.

Three terms, in the order they run:

- ``sessions_fold`` -- one live arm per connection the server holds open.
- ``session_for`` -- inside an arm, bind that connection's transport.
- ``run_once`` -- inside an arm, run the program at most once per connection.

The fold reads the server's connection book directly, so there is nothing
between a socket opening and an arm starting.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import nu
from nu.core.io import STDOUT
from nu.core.spans.bracket import _LifecycleBracket
from nustd.ui.core.session import Session

from .fabric import WebServer
from .refs import SID_ATTR, ServerRef


if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from nu.lang import Nu
    from nu.lang.runtime import Context


__all__ = [
    "SessionFor",
    "run_once",
    "session_for",
    "sessions_fold",
]


def sessions_fold(arm: Nu) -> Nu:
    """Run ``arm`` once per live connection, births and deaths included.

    Args:
        arm: the body one connection gets. Spawned when the connection
            appears in the server's book, cancelled and drained when it goes.
    """
    return nu.ForEachParReactive(
        ServerRef().sessions(),
        ServerRef().changed(),
        arm,
        SID_ATTR,
    )


class SessionFor(_LifecycleBracket):
    """Bind the ws transport of the connection this arm belongs to.

    Reads the sid off the Context the fold branched for this arm, looks the
    live session up in the server's connection book, and binds it under the
    abstract ``Session`` so every Ref underneath resolves through it. Nothing
    is torn down: the server owns the session and the endpoint closes it.

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
            # Transiently reachable: the browser can go away between the
            # connect and the fold's next pass. The arm raises, the fold
            # isolates it, and the next pass has no element to respawn.
            msg = f"no live ws session for {sid!r}"
            raise LookupError(msg)
        yield ctx.bind(Session, session)


def session_for(sid_attr: str = SID_ATTR, body: Nu | None = None) -> SessionFor:
    """``SessionFor`` in call order: the attr first, then what runs under it.

    Example:
        >>> session_for(SID_ATTR, run_once(App.boot() >> program))
    """
    return SessionFor(body, sid_attr=sid_attr)


def run_once(body: Nu, *, sid_attr: str = SID_ATTR) -> Nu:
    """Run ``body`` for this connection at most once, and mark it done after.

    The fold frees the key of every arm whose task has ended and respawns it,
    so a program that returns would be booted again on the next connect or
    disconnect. ``done`` on the connection is what a respawned arm reads to
    become a no-op. A failure is reported and marks done all the same, so a
    program that raises leaves a stopped tab instead of a retry loop.

    Args:
        body: what one connection runs, its boot frames included.
        sid_attr: the attr the fold parked this arm's session id under.

    Example:
        >>> session_for(SID_ATTR, run_once(App.boot() >> program))
    """
    sid = nu.StrAttrRef(sid_attr)
    report = nu.Print(
        STDOUT,
        nu.Str("nustd.ui session arm failed:"),
        nu.ToStr(nu.AttrRef("error")),
    )
    return nu.IfDo(
        nu.Not(ServerRef().done(sid)),
        nu.TryCatch(body, catch=report) >> ServerRef().mark_done(sid),
    )
