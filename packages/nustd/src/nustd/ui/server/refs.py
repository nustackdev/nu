"""``ServerRef`` and its atoms: the registry, reachable from inside the tree.

``ServerRef`` reads the bound ``WebServer`` off the Context, and its four
atoms are the whole surface the fold and its arms need -- the live session
ids, a subscription on connections opening and closing, and the read and the
write of one connection's ``done`` flag.

Plus ``SID_ATTR``, the name the fold parks each arm's session id under.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.context.fabric import FabricRef
from nu.engine.structure import Declared
from nu.lang import Command, ScalarQuery
from nu.lang.sentinels import EMPTY, INVALID

from .fabric import WebServer


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = [
    "SID_ATTR",
    "LiveSessions",
    "MarkSessionDone",
    "ServerRef",
    "SessionDone",
    "SessionsChanged",
]


#: What the fold binds each session id under. ``ForEachParReactive`` branches
#: ``ctx.attrs`` per arm, so a user attr of the same name is shadowed only
#: inside an arm, never across arms.
SID_ATTR = "sid"


_SYNC_UNSUPPORTED = "nustd.ui is async-only; use nu.arun"


class _ServerQuery(ScalarQuery):
    """A read off the ``WebServer`` a ``ServerRef`` in slot 0 resolves to.

    Subclasses answer from the server instance; every one of them yields
    INVALID when no server bracket is open around this subtree.
    """

    _requires_async = Declared(value=True, name="requires_async")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            raise RuntimeError(_SYNC_UNSUPPORTED)

        return thunk


class LiveSessions(_ServerQuery):
    """The session id of every connection the server currently holds open."""

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        server_thunk = children[0]

        async def athunk(rt: Runtime) -> object:
            server = await server_thunk(rt)
            if server is EMPTY or server is INVALID:
                return INVALID
            return server.live_ids()

        return athunk


class SessionsChanged(_ServerQuery):
    """Subscribe to connections opening and closing, on one ordered channel.

    Both moments ride the same subscription, so the open and the close of one
    sid can never be seen out of order. Nothing else emits on it, so a write
    into the registry does not wake whoever is bound.
    """

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        server_thunk = children[0]

        async def athunk(rt: Runtime) -> object:
            server = await server_thunk(rt)
            if server is EMPTY or server is INVALID:
                return INVALID
            return server.subscribe()

        return athunk


class SessionDone(_ServerQuery):
    """Whether the program of the connection at slot 1 has already ended.

    False for a sid the server does not hold: a closed socket has no arm
    left to guard.
    """

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        server_thunk, sid_thunk = children[0], children[1]

        async def athunk(rt: Runtime) -> object:
            server = await server_thunk(rt)
            if server is EMPTY or server is INVALID:
                return INVALID
            sid = await sid_thunk(rt)
            if sid is EMPTY or sid is INVALID:
                return INVALID
            return server.is_done(sid)

        return athunk


class MarkSessionDone(Command):
    """Record that the program of the connection at slot 1 has ended.

    A sid the server does not hold is a plain miss: nothing is created and
    nothing is announced.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")
    _requires_async = Declared(value=True, name="requires_async")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            raise RuntimeError(_SYNC_UNSUPPORTED)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        server_thunk, sid_thunk = children[0], children[1]

        async def athunk(rt: Runtime) -> None:
            server = await server_thunk(rt)
            if server is EMPTY or server is INVALID:
                return
            sid = await sid_thunk(rt)
            if sid is EMPTY or sid is INVALID:
                return
            server.mark_done(sid)

        return athunk


class ServerRef(FabricRef):
    """The ``WebServer`` bound on the Context, and the registry it holds.

    Reads as the server instance itself, EMPTY when no server bracket is open
    around this subtree.
    """

    fabric = WebServer

    def sessions(self) -> LiveSessions:
        """The ids of every live ws connection, as one list."""
        return LiveSessions(self)

    def changed(self) -> SessionsChanged:
        """A change source firing a sid per connection opened and closed."""
        return SessionsChanged(self)

    def done(self, sid: object) -> SessionDone:
        """Whether the program for ``sid`` has already ended."""
        return SessionDone(self, sid)

    def mark_done(self, sid: object) -> MarkSessionDone:
        """Record that the program for ``sid`` has ended."""
        return MarkSessionDone(self, sid)
