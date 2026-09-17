"""The ws host, in three layers plus a bracket.

1. ``fabric`` -- a server that boots uvicorn, binds itself, and stops on the
   way out. It owns the connection book and the two channels that announce a
   socket opening and closing. It never sees the UI program.
2. ``refs`` -- a kv shape holding one row per live connection, and the Refs
   that reach the server's channels from inside the tree.
3. ``driver`` -- the Nu terms that relay those channels into that shape, and
   the fold that runs one arm of the program per row.

Plus ``SessionFor``, the bracket that hands one arm the transport of the
connection it belongs to.

The split is the point. A fabric binds something and tears it down, nothing
more; the program is a child of the tree, where the tree can see it; and the
lifetime of an arm is the lifetime of a socket, in both directions -- a dying
arm cannot reach a browser, and a closed browser cancels its arm.
"""

from __future__ import annotations

from .driver import SessionFor, seed_sessions, session_driver, session_for, sessions_fold
from .fabric import WebServer, web_server
from .refs import (
    CONNECT_ATTR,
    DISCONNECT_ATTR,
    SID_ATTR,
    OnConnect,
    OnDisconnect,
    ServerRef,
    SessionRow,
    Sessions,
    WsSessions,
)
from .store import sessions_store


__all__ = [
    "CONNECT_ATTR",
    "DISCONNECT_ATTR",
    "SID_ATTR",
    "OnConnect",
    "OnDisconnect",
    "ServerRef",
    "SessionFor",
    "SessionRow",
    "Sessions",
    "WebServer",
    "WsSessions",
    "seed_sessions",
    "session_driver",
    "session_for",
    "sessions_fold",
    "sessions_store",
    "web_server",
]
