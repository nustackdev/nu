"""nustd.ws_server -- a websocket host, in three layers plus a bracket.

Generic connection lifecycle and nothing else: it knows sockets, not wire
formats. The session class handed to it owns the protocol end to end.

1. ``fabric`` -- a server that boots uvicorn, binds itself, and stops on the
   way out. It owns the book of live connections and the channel that
   announces that book moving.
2. ``ref`` -- ``ServerRef``, the server as a value inside the tree.
3. ``interactions`` -- every term that reaches the book: the live ids, the
   change subscription, one connection's ``done``, and ``SessionFor``, the
   bracket that hands an arm the transport of the connection it belongs to.
4. ``driver`` -- the fold that runs one arm of the program per connection.

Plus ``preset``, where ``listen`` stacks the bracket for a ``nu.With`` spec
slot. The lifetime of an arm is the lifetime of a socket, in both directions.
"""

from __future__ import annotations

from .driver import run_once, session_for, sessions_fold
from .fabric import SessionProtocol, WebServer
from .interactions import (
    SID_ATTR,
    LiveSessions,
    MarkSessionDone,
    SessionDone,
    SessionFor,
    SessionsChanged,
)
from .preset import listen
from .ref import ServerRef


__all__ = [
    "SID_ATTR",
    "LiveSessions",
    "MarkSessionDone",
    "ServerRef",
    "SessionDone",
    "SessionFor",
    "SessionProtocol",
    "SessionsChanged",
    "WebServer",
    "listen",
    "run_once",
    "session_for",
    "sessions_fold",
]
