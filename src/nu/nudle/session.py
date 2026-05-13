"""Per-connection session handle.

Bound on Context for the lifetime of one ws connection. The session owns
the ws, the observer registry, and the pending-read futures. Interactions
build Frames and call `send`; the session does no per-op work.

Analogous to a Navigator in nu-virtuals: the "storage" handle nudle Refs
resolve through. Here the storage is a ws and a browser tab.
"""

from __future__ import annotations

import asyncio
import uuid
from collections import defaultdict
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from .protocol import OP_ERROR, OP_MOUNT, OP_NOTIFY, OP_READ, OP_UNMOUNT, Frame, decode, encode


if TYPE_CHECKING:
    from fastapi import WebSocket


__all__ = ["NudleSession", "Subscription"]


Callback = Callable[[object], None]


class Subscription:
    """Observer handle returned by `session.subscribe(path)`.

    Same shape as nu-virtuals' subscription handle: `bind`, `unbind`,
    `close`. Wired so React/ReactForever can subscribe to ref notifications
    coming from the browser.
    """

    def __init__(self, session: NudleSession, path: str) -> None:
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


class NudleSession:
    """One ws connection, one mounted page."""

    def __init__(self, ws: WebSocket) -> None:
        self._ws = ws
        self._subs: dict[str, set[Subscription]] = defaultdict(set)
        self._pending: dict[str, asyncio.Future[Any]] = {}
        self._stopped = False

    # ---- outbound -----------------------------------------------------------

    async def send(self, frame: Frame) -> None:
        await self._ws.send_text(encode(frame))

    async def mount(self, page_name: str, fields: list[dict[str, str]]) -> None:
        payload = {"page": page_name, "fields": fields}
        await self.send(Frame(OP_MOUNT, ref="", payload=payload))

    async def aread(self, path: str) -> Any:
        """Round-trip read: ship a read frame, await the browser's reply."""
        rid = uuid.uuid4().hex
        loop = asyncio.get_running_loop()
        fut: asyncio.Future[Any] = loop.create_future()
        self._pending[rid] = fut
        try:
            await self.send(Frame(OP_READ, ref=path, payload=None, id=rid))
            return await fut
        finally:
            self._pending.pop(rid, None)

    def subscribe(self, path: str) -> Subscription:
        sub = Subscription(self, path)
        self._subs[path].add(sub)
        return sub

    # ---- intake -------------------------------------------------------------

    async def run_intake(self) -> None:
        """Drive the ws read loop, dispatch browser->server frames."""
        from fastapi import WebSocketDisconnect

        try:
            while not self._stopped:
                raw = await self._ws.receive_text()
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
        if frame.op in (OP_MOUNT, OP_UNMOUNT, OP_ERROR):
            # Browser may emit error frames; ignore for v0.1.0.
            return
        # Unknown inbound op: ignored for v0.1.0.

    def _fail_pending(self) -> None:
        for fut in self._pending.values():
            if not fut.done():
                fut.set_exception(ConnectionError("nudle session closed"))
        self._pending.clear()
