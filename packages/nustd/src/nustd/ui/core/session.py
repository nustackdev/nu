"""Session -- the wire transport Refs resolve through, plus the ws one.

A Session is the handle a Ref reaches the client through: send a Frame,
round-trip a read, subscribe to change notifications. The ABC is the seam, so
the widget kit does not know which host it is running under.

``WsSession`` is the concrete one, a Session over a FastAPI websocket, shared
by every ws host. It owns the ws, the observer registry and the pending-read
futures.

The host binds it (``ctx.bind(Session, concrete)``); widget code reads it back
with ``rt.ctx.get(Session)``.
"""

from __future__ import annotations

import asyncio
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Protocol

from .protocol import OP_ERROR, OP_NOTIFY, OP_READ, Frame, decode, encode


if TYPE_CHECKING:
    from fastapi import WebSocket


__all__ = ["Session", "Subscription", "WsSession", "WsSubscription"]


Callback = Callable[[object], None]


class Subscription(Protocol):
    """Observer handle returned by ``session.subscribe(path)``.

    Same shape as nu-kv's subscription handle: the session fires the bound
    callbacks when a ``notify`` frame lands for the subscribed path.
    """

    def bind(self, cb: Callable[[object], None]) -> None: ...

    def unbind(self, cb: Callable[[object], None]) -> None: ...

    def close(self) -> None: ...


class Session(ABC):
    """Abstract wire transport for a mounted UI.

    One instance per client connection. Owned by the host; bound on
    Context so Refs and interactions can reach it.
    """

    @abstractmethod
    async def send(self, frame: Frame) -> None:
        """Ship a Frame to the client."""

    @abstractmethod
    async def aread(self, path: tuple[str, ...]) -> Any:
        """Round-trip: ship a read frame, await the client's reply."""

    @abstractmethod
    def subscribe(self, path: tuple[str, ...]) -> Subscription:
        """Register interest in change notifications for `path`."""


class WsSubscription:
    """Observer handle returned by ``session.subscribe(path)``.

    Callbacks are held in a list and compared by identity, never hashed: one
    is often a reverse proxy into a worker process, and hashing it is a round
    trip over the wire that raises once the worker is gone.
    """

    def __init__(self, session: WsSession, path: tuple[str, ...]) -> None:
        self._session = session
        self._path = path
        self._callbacks: list[Callback] = []
        self._closed = False

    def bind(self, cb: Callback) -> None:
        """Register ``cb`` to fire on inbound notify frames for this path."""
        if self._closed:
            return
        if not any(cb is bound for bound in self._callbacks):
            self._callbacks.append(cb)

    def unbind(self, cb: Callback) -> None:
        """Drop a previously bound callback (idempotent)."""
        self._callbacks = [bound for bound in self._callbacks if bound is not cb]

    def close(self) -> None:
        """Detach from the session; further ``bind`` calls no-op."""
        if self._closed:
            return
        self._closed = True
        self._callbacks = []
        subs = self._session._subs.get(self._path)
        if subs is not None:
            subs.discard(self)
            if not subs:
                self._session._subs.pop(self._path, None)

    def _fire(self, payload: object) -> None:
        """Hand the payload to every bound callback, dropping the dead ones.

        A raise means the far end is gone -- usually a pool worker killed by a
        page restart with no chance to unbind -- so drop that callback rather
        than let one stale subscriber take the whole ws down.
        """
        dead: list[Callback] = []
        for cb in tuple(self._callbacks):
            try:
                cb(payload)
            except Exception:  # the far end is a dead process
                dead.append(cb)
        if dead:
            self._callbacks = [cb for cb in self._callbacks if not any(cb is gone for gone in dead)]


class WsSession(Session):
    """One ws connection, one browser tree."""

    # What a host binds an instance under, so every Ref underneath asks for the
    # abstract transport rather than this concrete one.
    _nu_bind_as = Session

    def __init__(self, ws: WebSocket) -> None:
        self._ws = ws
        self._subs: dict[tuple[str, ...], set[WsSubscription]] = defaultdict(set)
        self._pending: dict[str, asyncio.Future[Any]] = {}
        self._stopped = False

    # ---- outbound -----------------------------------------------------------

    async def send(self, frame: Frame) -> None:
        """Encode and ship one Frame on the ws."""
        await self._ws.send_bytes(encode(frame))

    async def aread(self, path: tuple[str, ...]) -> Any:
        """Round-trip read: ship a read frame, await the client's reply."""
        rid = uuid.uuid4().hex
        loop = asyncio.get_running_loop()
        fut: asyncio.Future[Any] = loop.create_future()
        self._pending[rid] = fut
        try:
            await self.send(Frame(OP_READ, ref=path, payload=None, id=rid))
            return await fut
        finally:
            self._pending.pop(rid, None)

    def subscribe(self, path: tuple[str, ...]) -> WsSubscription:
        """Return a Subscription observing notify frames for ``path``."""
        sub = WsSubscription(self, path)
        self._subs[path].add(sub)
        return sub

    # ---- intake -------------------------------------------------------------

    async def run_intake(self) -> None:
        """Drive the ws read loop, dispatch client->server frames."""
        from fastapi import WebSocketDisconnect

        try:
            while not self._stopped:
                raw = await self._ws.receive_bytes()
                frame = decode(raw)
                self._dispatch(frame)
        except WebSocketDisconnect:
            pass
        finally:
            self._stopped = True
            self._fail_pending()

    def _dispatch(self, frame: Frame) -> None:
        if frame.op == OP_NOTIFY:
            for sub in tuple(self._subs.get(frame.ref, ())):
                sub._fire(frame.payload)
            return
        if frame.op == OP_READ and frame.id is not None:
            fut = self._pending.get(frame.id)
            if fut is not None and not fut.done():
                fut.set_result(frame.payload)
            return
        if frame.op == OP_ERROR:
            # The browser may report one. Nothing here acts on it yet.
            return
        # Unknown inbound op: ignored.

    def _fail_pending(self) -> None:
        for fut in self._pending.values():
            if not fut.done():
                fut.set_exception(ConnectionError("ui session closed"))
        self._pending.clear()
