"""Watches: the browser hears which (path, event) someone on the server listens to."""

from __future__ import annotations

import asyncio

from nustd.ui.core.events import ANY, CHANGE, EVENT, INPUT
from nustd.ui.core.interactions import _Only
from nustd.ui.core.protocol import OP_NOTIFY, OP_UNWATCH, OP_WATCH, Frame, decode
from nustd.ui.core.session import WsSession


class _Ws:
    def __init__(self) -> None:
        self.sent: list[bytes] = []

    async def send_bytes(self, raw: bytes) -> None:
        self.sent.append(raw)


def _frames(ws: _Ws) -> list[tuple[str, tuple[str, ...], object]]:
    out = []
    for raw in ws.sent:
        frame = decode(raw)
        out.append((frame.op, tuple(frame.ref), frame.payload))
    return out


async def _settle() -> None:
    for _ in range(3):
        await asyncio.sleep(0)


def _watch(path: tuple[str, ...], event: str) -> tuple[str, tuple[str, ...], object]:
    return (OP_WATCH, path, {EVENT: event})


def _unwatch(path: tuple[str, ...], event: str) -> tuple[str, tuple[str, ...], object]:
    return (OP_UNWATCH, path, {EVENT: event})


def _session() -> tuple[WsSession, _Ws]:
    ws = _Ws()
    return WsSession(ws), ws  # type: ignore[arg-type]


def test_no_subscriber_no_frame():
    async def run():
        session, ws = _session()
        session.subscribe(("s",), CHANGE)
        await _settle()
        return ws.sent

    assert asyncio.run(run()) == []


def test_bind_sends_one_watch():
    async def run():
        session, ws = _session()
        session.subscribe(("s",), CHANGE).bind(lambda _: None)
        await _settle()
        return _frames(ws)

    assert asyncio.run(run()) == [_watch(("s",), CHANGE)]


def test_two_binds_one_watch():
    async def run():
        session, ws = _session()
        one = session.subscribe(("s",), CHANGE)
        two = session.subscribe(("s",), CHANGE)
        one.bind(lambda _: None)
        one.bind(lambda _: None)
        two.bind(lambda _: None)
        await _settle()
        return _frames(ws)

    assert asyncio.run(run()) == [_watch(("s",), CHANGE)]


def test_last_unbind_sends_unwatch():
    async def run():
        session, ws = _session()
        one = session.subscribe(("s",), CHANGE)
        two = session.subscribe(("s",), CHANGE)
        a, b = (lambda _: None), (lambda _: None)
        one.bind(a)
        two.bind(b)
        one.unbind(a)
        await _settle()
        before = _frames(ws)
        two.unbind(b)
        await _settle()
        return before, _frames(ws)

    before, after = asyncio.run(run())
    assert before == [_watch(("s",), CHANGE)]
    assert after == [_watch(("s",), CHANGE), _unwatch(("s",), CHANGE)]


def test_close_sends_unwatch():
    async def run():
        session, ws = _session()
        sub = session.subscribe(("s",), INPUT)
        sub.bind(lambda _: None)
        sub.close()
        sub.close()
        await _settle()
        return _frames(ws)

    assert asyncio.run(run()) == [_watch(("s",), INPUT), _unwatch(("s",), INPUT)]


def test_rebind_watches_again():
    async def run():
        session, ws = _session()
        sub = session.subscribe(("s",), CHANGE)
        cb = lambda _: None  # noqa: E731
        sub.bind(cb)
        sub.unbind(cb)
        sub.bind(cb)
        await _settle()
        return _frames(ws)

    assert asyncio.run(run()) == [
        _watch(("s",), CHANGE),
        _unwatch(("s",), CHANGE),
        _watch(("s",), CHANGE),
    ]


def test_every_event_watches_any():
    async def run():
        session, ws = _session()
        session.subscribe(("t",)).bind(lambda _: None)
        await _settle()
        return _frames(ws)

    assert asyncio.run(run()) == [_watch(("t",), ANY)]


def test_events_and_paths_count_apart():
    async def run():
        session, ws = _session()
        change = session.subscribe(("s",), CHANGE)
        change.bind(lambda _: None)
        session.subscribe(("s",), INPUT).bind(lambda _: None)
        session.subscribe(("t",), CHANGE).bind(lambda _: None)
        change.close()
        await _settle()
        return _frames(ws)

    assert asyncio.run(run()) == [
        _watch(("s",), CHANGE),
        _watch(("s",), INPUT),
        _watch(("t",), CHANGE),
        _unwatch(("s",), CHANGE),
    ]


def test_only_counts_on_its_event():
    """``Changed(ref, event)`` wraps the session's subscription; the watch is that event's."""

    async def run():
        session, ws = _session()
        only = _Only(session.subscribe(("s",), CHANGE), CHANGE)
        a, b = (lambda _: None), (lambda _: None)
        only.bind(a)
        only.bind(b)
        only.unbind(a)
        await _settle()
        before = _frames(ws)
        only.close()
        await _settle()
        return before, _frames(ws)

    before, after = asyncio.run(run())
    assert before == [_watch(("s",), CHANGE)]
    assert after == [_watch(("s",), CHANGE), _unwatch(("s",), CHANGE)]


def test_dead_callback_gives_the_watch_back():
    def dead(_: object) -> None:
        raise ConnectionError("worker gone")

    async def run():
        session, ws = _session()
        session.subscribe(("s",), CHANGE).bind(dead)
        session._dispatch(Frame(OP_NOTIFY, ref=("s",), payload={EVENT: CHANGE}))
        await _settle()
        return _frames(ws)

    assert asyncio.run(run()) == [_watch(("s",), CHANGE), _unwatch(("s",), CHANGE)]


def test_stopped_session_sends_nothing():
    async def run():
        session, ws = _session()
        session._stopped = True
        sub = session.subscribe(("s",), CHANGE)
        sub.bind(lambda _: None)
        sub.close()
        await _settle()
        return ws.sent

    assert asyncio.run(run()) == []


def test_close_with_no_loop_does_not_raise():
    async def bind():
        session, ws = _session()
        sub = session.subscribe(("s",), CHANGE)
        sub.bind(lambda _: None)
        await _settle()
        return sub, ws

    sub, ws = asyncio.run(bind())
    sub.close()
    assert _frames(ws) == [_watch(("s",), CHANGE)]


def test_a_send_after_bind_goes_after_its_watch():
    """An upload read binds on its answer's event, then sends the command."""

    async def run():
        session, ws = _session()
        _Only(session.subscribe(("u",), "slice"), "slice").bind(lambda _: None)
        await session.send(Frame("slice", ref=("u",), payload={"start": 0}))
        await _settle()
        return _frames(ws)

    assert asyncio.run(run()) == [
        _watch(("u",), "slice"),
        ("slice", ("u",), {"start": 0}),
    ]


def test_a_send_after_close_goes_after_its_unwatch():
    async def run():
        session, ws = _session()
        sub = session.subscribe(("s",), CHANGE)
        sub.bind(lambda _: None)
        sub.close()
        await session.send(Frame("write", ref=("s",), payload=1))
        await _settle()
        return _frames(ws)

    assert asyncio.run(run()) == [
        _watch(("s",), CHANGE),
        _unwatch(("s",), CHANGE),
        ("write", ("s",), 1),
    ]
