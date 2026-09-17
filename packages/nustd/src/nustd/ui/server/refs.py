"""The sessions shape, the attr names, and the Refs that reach the server.

Three things the rest of the package addresses itself through:

- ``Sessions`` -- one kv row per live browser connection. A row, not a flag:
  the fold over it births an arm when a row appears and cancels that arm when
  the row goes, so presence is the whole of the state.
- the attr names the fold and the driver park their loop variables under.
- ``ServerRef``, which reads the bound ``WebServer`` off the Context, plus
  the two queries that hand its connect / disconnect channels to a reactive
  atom.

The channel queries are the seam between a socket and the tree. The FastAPI
endpoint runs with no Nu runtime around it, so it cannot write kv; it emits
onto a channel, and a Nu term subscribed through one of these performs the
write. Only Nu writes to kv.
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

    A row, not a flag -- the fold births an arm when the row appears and
    cancels it when the row goes, so there is nothing here for anyone to
    switch. ``sid`` is written only so the row has a leaf to materialize it;
    a shape row cannot exist with nothing under it.
    """

    sid = nustd.kv.StrRef.slot()


class Sessions(nu.Shape):
    """Root of the sessions store, and the tag its navigator binds under.

    The shape class is the tag: a Ref carries its root shape as the scope it
    resolves the Navigator under, so declaring the sessions shape apart from
    the app's is the whole of the routing.

    ``ShapesDictRef`` and not ``DictRef``, which is not cosmetic. As a
    container, creating a row fires the children subscription once for that
    key, a later write to a field inside the row fires nothing, and deleting
    the key fires again. With a plain dict the row key *is* the leaf, so every
    write into a row would look like the collection changing and restart that
    tab's whole app.
    """

    live = nustd.kv.ShapesDictRef.slot(SessionRow)


#: The sessions collection itself. What the driver writes and the fold folds.
WsSessions = Sessions.live


#: What the fold binds each session id under, inside the arm's own branch.
#: ``ForEachParReactive`` branches ``ctx.attrs`` per arm, so this shadows a
#: user attr of the same name only inside an arm, and never across arms.
SID_ATTR = "sid"

#: Where each driver arm parks the id its event carried. Two names, not one:
#: ``ParallelAsync`` does not branch ``ctx.attrs``, so two arms sharing a name
#: would read each other's event.
CONNECT_ATTR = "_ui_connect_sid"
DISCONNECT_ATTR = "_ui_disconnect_sid"


class _ServerChannel(ScalarQuery):
    """Yield one of the server's channels, for a reactive atom to drive.

    Holds a ``ServerRef`` in a read slot, the same shape ``Changed`` has, and
    resolves to the object that channel is. Nothing is subscribed here and no
    frame goes out: the atom above binds its own receiver on what comes back.

    A channel is not a kv view and has no observer behind it. It does not need
    one -- the whole reactive contract is ``bind`` / ``unbind`` / ``close``,
    and no atom ever inspects options or reaches for an observer, so the
    server's own fan-out object is a first-class change source.
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
