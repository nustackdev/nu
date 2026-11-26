"""The Nu side of a connection: fold over the live ones, hand each its session.

Three terms, in the order they run:

- ``sessions_fold`` -- one live arm per connection the server holds open.
- ``session_for`` -- inside an arm, bind that connection's transport and
  its id, read as ``SessionId.sid``.
- ``run_once`` -- inside an arm, run the program at most once per connection.

The fold reads the server's connection book directly, so there is nothing
between a socket opening and an arm starting.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import nu
from nu.core.io import STDOUT

from ..session import SessionId
from .interactions import SessionFor
from .ref import ServerRef


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang import Nu, StrArg


__all__ = [
    "run_once",
    "session_for",
    "sessions_fold",
]


def sessions_fold(arm: Nu | Callable[..., Nu]) -> Nu:
    """Run ``arm`` once per live connection, births and deaths included.

    Args:
        arm: the body one connection gets, a lambda over the connection's
            session id (hand it to ``session_for``). Spawned when the
            connection appears in the server's book, cancelled and drained
            when it goes.

    Notes:
        - No re-checks: the server signals opens and closes in process, on
          one channel that drops nothing, so a notification is never missed.
        - Each arm runs on a frame of its own, so arms never see each
          other's id.

    Example:
        sessions_fold(lambda sid: session_for(sid, run_once(program)))
    """
    return nu.ReconcileLatestEach(ServerRef().sessions(), ServerRef().on_change(), arm)


def session_for(sid: StrArg, body: Nu | None = None) -> SessionFor:
    """``SessionFor`` in call order: the session id first, then what runs under it.

    The body reads the id as ``SessionId.sid``.

    Example:
        sessions_fold(lambda sid: session_for(sid, run_once(program)))
    """
    return SessionFor(body, sid=sid)


def run_once(body: Nu) -> Nu:
    """Run ``body`` for this connection at most once, and mark it done after.

    The fold frees the key of every arm whose task has ended and respawns it,
    so a program that returns would be booted again on the next connect or
    disconnect. ``done`` on the connection is what a respawned arm reads to
    become a no-op. A failure is reported and marks done all the same, so a
    program that raises leaves a stopped connection instead of a retry loop.

    Args:
        body: what one connection runs, whatever it sends at connect included.
            Runs inside ``session_for``, whose id it reads.

    Example:
        sessions_fold(lambda sid: session_for(sid, run_once(program)))
    """
    sid = SessionId.sid

    def report(error: Nu) -> Nu:
        return nu.Print(STDOUT, nu.Str("ws session arm failed:"), nu.ToStr(error))

    return nu.IfDo(
        nu.Not(ServerRef().done(sid)),
        nu.TryCatch(body, catch=report) >> ServerRef().mark_done(sid),
    )
