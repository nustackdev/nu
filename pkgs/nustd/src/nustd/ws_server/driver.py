"""The Nu side of a connection: fold over the live ones, hand each its session.

Three terms, in the order they run:

- ``sessions_fold`` -- one live arm per connection the server holds open.
- ``session_for`` -- inside an arm, bind that connection's transport.
- ``run_once`` -- inside an arm, run the program at most once per connection.

The fold reads the server's connection book directly, so there is nothing
between a socket opening and an arm starting.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import nu
from nu.core.io import STDOUT

from .interactions import SID_ATTR, SessionFor
from .ref import ServerRef


if TYPE_CHECKING:
    from nu.lang import Nu


__all__ = [
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
        ServerRef().on_change(),
        arm,
        SID_ATTR,
    )


def session_for(sid_attr: str = SID_ATTR, body: Nu | None = None) -> SessionFor:
    """``SessionFor`` in call order: the attr first, then what runs under it.

    Example:
        >>> session_for(SID_ATTR, run_once(program))
    """
    return SessionFor(body, sid_attr=sid_attr)


def run_once(body: Nu, *, sid_attr: str = SID_ATTR) -> Nu:
    """Run ``body`` for this connection at most once, and mark it done after.

    The fold frees the key of every arm whose task has ended and respawns it,
    so a program that returns would be booted again on the next connect or
    disconnect. ``done`` on the connection is what a respawned arm reads to
    become a no-op. A failure is reported and marks done all the same, so a
    program that raises leaves a stopped connection instead of a retry loop.

    Args:
        body: what one connection runs, whatever it sends at connect included.
        sid_attr: the attr the fold parked this arm's session id under.

    Example:
        >>> session_for(SID_ATTR, run_once(program))
    """
    sid = nu.StrAttrRef(sid_attr)
    report = nu.Print(
        STDOUT,
        nu.Str("ws session arm failed:"),
        nu.ToStr(nu.AttrRef("error")),
    )
    return nu.IfDo(
        nu.Not(ServerRef().done(sid)),
        nu.TryCatch(body, catch=report) >> ServerRef().mark_done(sid),
    )
