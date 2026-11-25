"""A batch frame: notifies the browser queued together, fired in order."""

from __future__ import annotations

import asyncio

from nustd.ui.core.events import CHANGE, CLICK, EVENT, INPUT
from nustd.ui.core.protocol import OP_BATCH, OP_NOTIFY, Frame, decode, encode
from nustd.ui.core.session import WsSession


class _Ws:
    def __init__(self) -> None:
        self.sent: list[bytes] = []

    async def send_bytes(self, raw: bytes) -> None:
        self.sent.append(raw)


def _wire(frame: Frame) -> Frame:
    """The frame as it comes off the socket."""
    return decode(encode(frame))


def _listen(session: WsSession, *paths: tuple[str, ...]) -> list:
    seen: list = []
    for path in paths:
        session.subscribe(path).bind(lambda p, path=path: seen.append((path, p)))
    return seen


def test_batch_fires_each_pair_in_order():
    async def run():
        session = WsSession(_Ws())  # type: ignore[arg-type]
        seen = _listen(session, ("s",), ("b",))
        pairs = [
            [["s"], {EVENT: INPUT, "value": 1}],
            [["s"], {EVENT: INPUT, "value": 2}],
            [["b"], {EVENT: CLICK}],
            [["s"], {EVENT: CHANGE, "value": 2}],
        ]
        session._dispatch(_wire(Frame(OP_BATCH, payload=pairs)))
        return seen

    assert asyncio.run(run()) == [
        (("s",), {EVENT: INPUT, "value": 1}),
        (("s",), {EVENT: INPUT, "value": 2}),
        (("b",), {EVENT: CLICK}),
        (("s",), {EVENT: CHANGE, "value": 2}),
    ]


def test_batch_pair_fires_like_a_notify():
    async def run():
        session = WsSession(_Ws())  # type: ignore[arg-type]
        seen = _listen(session, ("p", "w"))
        payload = {EVENT: INPUT, "value": "ab"}
        session._dispatch(_wire(Frame(OP_NOTIFY, ref=("p", "w"), payload=payload)))
        session._dispatch(_wire(Frame(OP_BATCH, payload=[[["p", "w"], payload]])))
        return seen

    first, second = asyncio.run(run())
    assert first == second


def test_batch_skips_refs_nobody_listens_to():
    async def run():
        session = WsSession(_Ws())  # type: ignore[arg-type]
        seen = _listen(session, ("b",))
        pairs = [[["gone"], {EVENT: INPUT}], [["b"], {EVENT: CLICK}]]
        session._dispatch(_wire(Frame(OP_BATCH, payload=pairs)))
        session._dispatch(_wire(Frame(OP_BATCH, payload=[])))
        return seen

    assert asyncio.run(run()) == [(("b",), {EVENT: CLICK})]
