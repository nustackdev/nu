"""Per-connection session handle.

Bound on Context for the lifetime of one ws connection. nudle commands
resolve a NudleSession from Context and call .awrite / .aappend on it;
those send a Frame on the wire.

This is the analogue of a parent view in nu-virtuals: the "storage" for
nudle Refs. The storage just happens to be a websocket.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .protocol import OP_MOUNT, Frame, encode


if TYPE_CHECKING:
    from fastapi import WebSocket


__all__ = ["NudleSession"]


class NudleSession:
    """One ws connection, one mounted page."""

    def __init__(self, ws: WebSocket) -> None:
        self._ws = ws

    async def _send(self, frame: Frame) -> None:
        await self._ws.send_text(encode(frame))

    async def mount(self, page_name: str, fields: list[tuple[str, str]]) -> None:
        payload = {
            "page": page_name,
            "fields": [{"path": p, "type": t} for p, t in fields],
        }
        await self._send(Frame(op=OP_MOUNT, ref="", payload=payload))

    async def awrite(self, path: str, value: Any) -> None:
        await self._send(Frame(op="write", ref=path, payload=value))

    async def aappend(self, path: str, value: Any) -> None:
        await self._send(Frame(op="append", ref=path, payload=value))
