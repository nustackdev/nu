"""NudleSession -- Session implementation over a FastAPI websocket.

Bound on Context for the lifetime of one ws connection. Owns the ws,
the observer registry, and the pending-read futures. Interactions build
Frames and call `send`; the session does no per-op work.

Concrete implementation of ``nustd.ui.core.session.Session`` -- the abstract
transport interface widgets and interactions target.
"""

from __future__ import annotations

import asyncio
import uuid
from collections import defaultdict
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from nustd.ui.core.protocol import (
    OP_ERROR,
    OP_INIT,
    OP_NOTIFY,
    OP_READ,
    OP_REMOVE,
    OP_WRITE,
    Frame,
    decode,
    encode,
)
from nustd.ui.core.session import Session


if TYPE_CHECKING:
    from collections.abc import Sequence

    from fastapi import WebSocket


__all__ = ["NudleSession", "Subscription"]


Callback = Callable[[object], None]


class Subscription:
    """Observer handle returned by ``session.subscribe(path)``.

    Concrete implementation of ``nustd.ui.core.session.Subscription``.
    React / ReactForever bind callbacks on it; the session fires them
    when a ``notify`` frame lands for the subscribed path.
    """

    def __init__(self, session: NudleSession, path: tuple[str, ...]) -> None:
        self._session = session
        self._path = path
        self._callbacks: set[Callback] = set()
        self._closed = False

    def bind(self, cb: Callback) -> None:
        if self._closed:
            return
        self._callbacks.add(cb)

    def unbind(self, cb: Callback) -> None:
        self._callbacks.discard(cb)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._callbacks.clear()
        subs = self._session._subs.get(self._path)
        if subs is not None:
            subs.discard(self)
            if not subs:
                self._session._subs.pop(self._path, None)

    def _fire(self, payload: object) -> None:
        for cb in tuple(self._callbacks):
            cb(payload)


class NudleSession(Session):
    """One ws connection, one browser tree."""

    def __init__(self, ws: WebSocket) -> None:
        self._ws = ws
        self._subs: dict[tuple[str, ...], set[Subscription]] = defaultdict(set)
        self._pending: dict[str, asyncio.Future[Any]] = {}
        self._stopped = False

    # ---- outbound -----------------------------------------------------------

    async def send(self, frame: Frame) -> None:
        await self._ws.send_bytes(encode(frame))

    async def boot(
        self,
        name: str,
        chains: Sequence[tuple[tuple[str, str, dict[str, Any]], ...]],
        *,
        sidebar: bool = False,
    ) -> None:
        """Seed the browser's tree: app chrome on the root, then every slot.

        No envelope. The root write carries what the shell itself needs (the
        app name, whether the built-in sidebar is on) and each chain goes
        out as an `init`, which is the same walk a write takes minus the
        payload. Order is declaration order, which is render order.

        The clearing remove goes first because a reconnect gets a fresh
        session with none of the old one's dynamic nodes, and those would
        otherwise sit there forever.
        """
        await self.send(Frame(OP_REMOVE))
        await self.send(Frame(OP_WRITE, payload={"name": name, "sidebar": sidebar}))
        for chain in chains:
            await self.send(Frame(OP_INIT, ref=[seg for seg, _, _ in chain], chain=chain))

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

    def subscribe(self, path: tuple[str, ...]) -> Subscription:
        sub = Subscription(self, path)
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
            # Client may emit error frames; ignore for v0.1.0.
            return
        # Unknown inbound op: ignored for v0.1.0.

    def _fail_pending(self) -> None:
        for fut in self._pending.values():
            if not fut.done():
                fut.set_exception(ConnectionError("nudle session closed"))
        self._pending.clear()
