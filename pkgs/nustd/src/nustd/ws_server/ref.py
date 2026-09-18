"""``ServerRef`` -- the running ``WebServer``, reachable from inside the tree.

Its four methods are the whole surface the fold and its arms need: the live
session ids, a subscription on connections opening and closing, and the read
and the write of one connection's ``done`` flag.
"""

from __future__ import annotations

from nu.context.fabric import FabricRef

from .fabric import WebServer
from .interactions import LiveSessions, MarkSessionDone, SessionDone, SessionsChanged


__all__ = ["ServerRef"]


class ServerRef(FabricRef):
    """The ``WebServer`` bound on the Context, and the registry it holds.

    Reads as the server instance itself, EMPTY when no server bracket is open
    around this subtree.
    """

    fabric = WebServer

    def sessions(self) -> LiveSessions:
        """The ids of every live ws connection, as one list."""
        return LiveSessions(self)

    def on_change(self) -> SessionsChanged:
        """A change source firing a sid per connection opened and closed."""
        return SessionsChanged(self)

    def done(self, sid: object) -> SessionDone:
        """Whether the program for ``sid`` has already ended."""
        return SessionDone(self, sid)

    def mark_done(self, sid: object) -> MarkSessionDone:
        """Record that the program for ``sid`` has ended."""
        return MarkSessionDone(self, sid)
