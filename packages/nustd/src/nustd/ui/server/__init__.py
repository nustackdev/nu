"""The ws host, in three layers plus a bracket.

1. ``fabric`` -- a server that boots uvicorn, binds itself, and stops on the
   way out. It owns the book of live connections and the channel that
   announces that book moving. It never sees the UI program.
2. ``refs`` -- ``ServerRef`` and the atoms that reach the book from inside the
   tree: the live ids, the change subscription, and one connection's ``done``.
3. ``driver`` -- the fold that runs one arm of the program per connection.

Plus ``SessionFor``, the bracket that hands one arm the transport of the
connection it belongs to. The lifetime of an arm is the lifetime of a socket,
in both directions.
"""

from __future__ import annotations

from .driver import SessionFor, run_once, session_for, sessions_fold
from .fabric import WebServer, web_server
from .refs import (
    SID_ATTR,
    LiveSessions,
    MarkSessionDone,
    ServerRef,
    SessionDone,
    SessionsChanged,
)


__all__ = [
    "SID_ATTR",
    "LiveSessions",
    "MarkSessionDone",
    "ServerRef",
    "SessionDone",
    "SessionFor",
    "SessionsChanged",
    "WebServer",
    "run_once",
    "session_for",
    "sessions_fold",
    "web_server",
]
