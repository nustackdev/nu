"""The Nu side of a connection: relay it in, fold over it, hand it its session.

Five terms, in the order they run:

- ``seed_sessions`` -- create the registry collection before anyone watches it.
- ``session_driver`` -- turn the server's connect / disconnect moments into
  rows appearing and disappearing.
- ``sessions_fold`` -- one live arm per row.
- ``session_for`` -- inside an arm, bind that connection's transport.
- ``run_once`` -- inside an arm, run the program at most once per connection.

The ws endpoint has no Nu runtime around it, so it announces and Nu does the
kv write. Each term spells out its own storage bracket rather than leaning on
``auto_flow_atomic``.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import nu
import nustd.kv
from nu.core.io import STDOUT
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
    "run_once",
    "seed_sessions",
    "session_driver",
    "session_for",
    "sessions_fold",
]


def seed_sessions(*, scope: type[nu.Shape] = Sessions) -> Nu:
    """Bring the registry collection into being. Runs before anything watches it.

    A subscription over a container that is not there resolves to INVALID and
    never fires again, so this has to land ahead of the fold, not beside it.

    Args:
        scope: the registry shape, as the tag its storage resolves under.
    """
    # `create()` and never a plain `{}`: a literal is captured once when the
    # Form is built and would then be shared by every evaluation.
    return nustd.kv.Transaction(WsSessions.init(nu.Dict.create()), scope=scope)


def session_driver(*, scope: type[nu.Shape] = Sessions) -> Nu:
    """Relay the server's connect / disconnect moments into the registry.

    Two arms, forever. A connection writes its row; a disconnection deletes
    it. The key's presence is the whole of the state, so there is no flag on
    either side to set.

    Args:
        scope: the registry shape, as the tag its storage resolves under.
    """
    connected = nu.StrAttrRef(CONNECT_ATTR)
    gone = nu.StrAttrRef(DISCONNECT_ATTR)
    # `changed_key` parks the fired sid on `ctx.attrs` before each body run,
    # which is how it reaches the write. A `Transaction` per arm so the row
    # lands whole -- otherwise the fold spawns an arm over a half-built one.
    return nu.ParallelAsync(
        nu.ReactForever(
            ServerRef().on_connect(),
            nustd.kv.Transaction(
                WsSessions[connected].sid.set(connected),
                scope=scope,
            ),
            changed_key=CONNECT_ATTR,
        ),
        nu.ReactForever(
            ServerRef().on_disconnect(),
            nustd.kv.Transaction(WsSessions.del_item(gone), scope=scope),
            changed_key=DISCONNECT_ATTR,
        ),
    )


def sessions_fold(arm: Nu, *, scope: type[nu.Shape] = Sessions) -> Nu:
    """Run ``arm`` once per live connection, births and deaths included.

    Args:
        arm: the body one connection gets. Spawned when its row appears,
            cancelled and drained when the row goes.
        scope: the registry shape, as the tag its storage resolves under.
    """
    # `nu.list` and not the lazy view: the fold is a Flow, so the items slot's
    # snapshot closes the moment that thunk returns and a lazy view handed out
    # of it dies on first read. `Snapshot` and not `Transaction` since both
    # slots only read, tagged at `scope` so an untagged `auto_flow_atomic` pass
    # over an enclosing tree leaves them alone.
    ids = nustd.kv.Snapshot(nu.list(WsSessions.keys()), scope=scope)
    # Children-change is length exact; the generic filter is an unbounded
    # prefix, so a write inside one row would restart that tab's whole app.
    changed = nustd.kv.Snapshot(WsSessions.on_children_change(), scope=scope)
    return nu.ForEachParReactive(ids, changed, arm, SID_ATTR)


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
            # isolates it, the row delete lands next pass. One wasted spawn.
            msg = f"no live ws session for {sid!r}"
            raise LookupError(msg)
        yield ctx.bind(Session, session)


def session_for(sid_attr: str = SID_ATTR, body: Nu | None = None) -> SessionFor:
    """``SessionFor`` in call order: the attr first, then what runs under it.

    Example:
        >>> session_for(SID_ATTR, run_once(App.boot() >> program))
    """
    return SessionFor(body, sid_attr=sid_attr)


def run_once(
    body: Nu,
    *,
    scope: type[nu.Shape] = Sessions,
    sid_attr: str = SID_ATTR,
) -> Nu:
    """Run ``body`` for this connection at most once, and mark the row done after.

    The fold frees the key of every arm whose task has ended and respawns it,
    so a program that returns would be booted again on the next connect or
    disconnect. ``done`` on the row is what a respawned arm reads to become a
    no-op. A failure is reported and marks done all the same, so a program
    that raises leaves a stopped tab instead of a retry loop.

    Args:
        body: what one connection runs, its boot frames included.
        scope: the registry shape, as the tag its storage resolves under.
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
    # Guarded on the row from inside the same transaction: a socket that shut
    # while the program was ending has had its row deleted, and a plain write
    # would vivify it back. A vivifying write is also the one kind the
    # length-exact children filter sees, so the fold would spawn over it.
    mark_done = nustd.kv.Transaction(
        nu.IfDo(WsSessions.contains(sid), WsSessions[sid].done.set(True)),
        scope=scope,
    )
    return nu.IfDo(
        nustd.kv.Snapshot(WsSessions[sid].done.missing(), scope=scope),
        nu.TryCatch(body, catch=report) >> mark_done,
    )
