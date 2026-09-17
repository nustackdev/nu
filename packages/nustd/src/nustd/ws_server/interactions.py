"""Every term that reaches the connection book, and the bracket that opens one.

The four atoms take a ``ServerRef`` in slot 0 and read the ``WebServer`` it
resolves to, yielding INVALID when no server bracket is open around this
subtree. ``SessionFor`` is the bracket an arm runs inside, holding that
connection's transport.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from nu.core.spans.bracket import _LifecycleBracket
from nu.engine.structure import Declared
from nu.lang import Command, ScalarQuery
from nu.lang.sentinels import EMPTY, INVALID

from .fabric import WebServer


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable

    from nu.lang import Nu
    from nu.lang.runtime import Context, Runtime


__all__ = [
    "SID_ATTR",
    "LiveSessions",
    "MarkSessionDone",
    "SessionDone",
    "SessionFor",
    "SessionsChanged",
]


#: What the fold binds each session id under. ``ForEachParReactive`` branches
#: ``ctx.attrs`` per arm, so a user attr of the same name is shadowed only
#: inside an arm, never across arms.
SID_ATTR = "sid"


_SYNC_UNSUPPORTED = "nustd.ws_server is async-only; use nu.arun"


class _ServerQuery(ScalarQuery):
    """A read off the ``WebServer`` a ``ServerRef`` in slot 0 resolves to."""

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


class SessionFor(_LifecycleBracket):
    """Bind the ws transport of the connection this arm belongs to.

    Reads the sid off the Context the fold branched for this arm, looks the
    live session up in the server's connection book, and binds it under the
    session class's ``_nu_bind_as`` -- the abstract type the protocol's terms
    ask for -- falling back to the concrete class when there is none. Nothing
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
            # isolates it, and the next pass has no element to respawn.
            msg = f"no live ws session for {sid!r}"
            raise LookupError(msg)
        cls = type(session)
        yield ctx.bind(getattr(cls, "_nu_bind_as", None) or cls, session)
