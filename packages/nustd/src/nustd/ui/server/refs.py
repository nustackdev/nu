"""The sessions shape, the attr names, and the Refs that reach the server.

Three things the rest of the package addresses itself through:

- ``Sessions`` -- one kv row per live browser connection.
- the attr names the fold and the driver park their loop variables under.
- ``ServerRef``, which reads the bound ``WebServer`` off the Context, plus
  the two queries that hand its connect / disconnect channels to a reactive
  atom.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import nu
import nustd.kv
from nu.context.fabric import FabricRef
from nu.engine.structure import Declared
from nu.lang import ScalarQuery
from nu.lang.sentinels import EMPTY, INVALID

from .fabric import WebServer


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = [
    "CONNECT_ATTR",
    "DISCONNECT_ATTR",
    "SID_ATTR",
    "OnConnect",
    "OnDisconnect",
    "ServerRef",
    "SessionRow",
    "Sessions",
    "WsSessions",
]


class SessionRow(nu.Shape):
    """One live browser connection, as one row the fold can count.

    The fold births an arm when the row appears and cancels it when the row
    goes, so presence is most of the state. ``sid`` is written only so the row
    has a leaf to materialize it; ``done`` says the program for this
    connection has ended and must not be started again.
    """

    sid = nustd.kv.StrRef.slot()
    done = nustd.kv.BoolRef.slot()


class Sessions(nu.Shape):
    """Root of the sessions store, and the tag its navigator binds under.

    A Ref carries its root shape as the scope it resolves the Navigator
    under, so declaring this apart from the app's shape is the whole of the
    routing.

    ``ShapesDictRef`` so a row is a container: creating and deleting a key
    fires the children subscription, a write to a field inside a row fires
    nothing. A plain dict would make every such write look like the
    collection changing and restart that tab's whole app.
    """

    live = nustd.kv.ShapesDictRef.slot(SessionRow)


#: The sessions collection itself. What the driver writes and the fold folds.
WsSessions = Sessions.live


#: What the fold binds each session id under. ``ForEachParReactive`` branches
#: ``ctx.attrs`` per arm, so a user attr of the same name is shadowed only
#: inside an arm, never across arms.
SID_ATTR = "sid"

#: Where each driver arm parks the id its event carried. Two names, not one:
#: ``ParallelAsync`` does not branch ``ctx.attrs``, so two arms sharing a name
#: would read each other's event.
CONNECT_ATTR = "_ui_connect_sid"
DISCONNECT_ATTR = "_ui_disconnect_sid"


class _ServerChannel(ScalarQuery):
    """Yield one of the server's channels, for a reactive atom to drive.

    Holds a ``ServerRef`` in a read slot and resolves to the channel object.
    Nothing is subscribed here and no frame goes out: the atom above binds its
    own receiver on what comes back.
    """

    _requires_async = Declared(value=True, name="requires_async")

    #: The ``WebServer`` accessor each subclass names.
    _channel: ClassVar[str] = ""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            raise RuntimeError("nustd.ui is async-only; use nu.arun")

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        server_thunk = children[0]
        channel = type(self)._channel

        async def athunk(rt: Runtime) -> object:
            server = await server_thunk(rt)
            if server is EMPTY or server is INVALID:
                return INVALID
            return getattr(server, channel)()

        return athunk


class OnConnect(_ServerChannel):
    """Fires one session id per accepted ws connection."""

    _channel = "on_connect"


class OnDisconnect(_ServerChannel):
    """Fires one session id per closed ws connection."""

    _channel = "on_disconnect"


class ServerRef(FabricRef):
    """The ``WebServer`` bound on the Context, and the way to its channels.

    Reads as the server instance itself, EMPTY when no server bracket is open
    around this subtree.
    """

    fabric = WebServer

    def on_connect(self) -> OnConnect:
        """A change source firing the sid of each new ws connection."""
        return OnConnect(self)

    def on_disconnect(self) -> OnDisconnect:
        """A change source firing the sid of each ws connection that closed."""
        return OnDisconnect(self)
