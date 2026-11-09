"""Tests for the Stream flow: drain-then-follow over ordered collections.

Construction checks run without a substrate. The drain/follow loop is driven
through the compiled thunk with an in-memory log and a hand-fired ``Feed``; a
run over a real ordered-collection substrate is deferred.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest
from _support.reactive import Feed, live_rechecks, until

import nu
from nu.core.reactive.cursor.stream import Stream
from nu.domains.shape.collections.abc.sequence import SequenceRef
from nu.lang import Context, Literal, StreamQuery


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


# ---------------------------------------------------------------------------
# Class hierarchy
# ---------------------------------------------------------------------------


def test_stream_is_stream_query():
    assert issubclass(Stream, StreamQuery)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_stream_constructs_with_source_and_body():
    source = SequenceRef("items")
    body = SequenceRef("body")
    s = Stream(source, body)
    # advance + change + body + key + log_key + after + every = 7 children
    assert len(nu.tree.children(s)) == 7


def test_stream_constructs_with_custom_keys():
    source = SequenceRef("items")
    body = SequenceRef("body")
    s = Stream(source, body, key="my_key", log_key="my_log_key")
    assert len(nu.tree.children(s)) == 7


def test_stream_refuses_a_literal_schedule_that_cannot_run():
    with pytest.raises(ValueError, match="Stream: every= must be positive"):
        Stream(SequenceRef("items"), SequenceRef("body"), every=0)
    with pytest.raises(ValueError, match="Stream: after= delays must not be negative"):
        Stream(SequenceRef("items"), SequenceRef("body"), after=(-1,))


# ---------------------------------------------------------------------------
# Sync compile raises (async-only)
# ---------------------------------------------------------------------------


def test_stream_sync_thunk_raises():
    s = Stream(SequenceRef("items"), SequenceRef("body"))
    with pytest.raises(RuntimeError, match="Stream requires an async runtime; use arun"):
        s._compile(0, ())(None)


# ---------------------------------------------------------------------------
# Execution deferred
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="substrate impl deferred: needs real ordered collection backing store")
async def test_stream_drains_existing_items():
    pass


@pytest.mark.skip(reason="substrate impl deferred: needs real ordered collection backing store")
async def test_stream_follows_new_items():
    pass


# ---------------------------------------------------------------------------
# Driven through the compiled thunk with hand-made children: an in-memory log
# behind ``advance`` and a hand-fired ``Feed`` behind ``change``
# ---------------------------------------------------------------------------


class _Log:
    """An append-only log read through a cursor; appending notifies like a writer would."""

    def __init__(self, feed: Feed, items: list | None = None) -> None:
        self.items = list(items or [])
        self.feed = feed
        self.read = 0
        self.order: list = []
        self.on_exhausted: Callable[[], None] | None = None

    def append(self, item: object) -> None:
        self.items.append(item)
        self.feed.fire(len(self.items) - 1)  # only a bound receiver hears it

    async def advance(self, rt: object) -> object:
        if self.read < len(self.items):
            self.read += 1
            self.order.append("advance")
            return (f"log-{self.read}", self.items[self.read - 1])
        if self.on_exhausted is not None:
            hook, self.on_exhausted = self.on_exhausted, None
            hook()
        return None


async def _const(value: object) -> object:
    return value


def _children(log: _Log, *, after: tuple = (), every: float | None = None) -> tuple:
    async def change(rt: object) -> Feed:
        log.order.append("subscribe")
        return log.feed

    async def body(rt: Runtime) -> object:
        return [rt.ctx.attrs.get("key")]

    return (
        log.advance,
        change,
        body,
        lambda rt: _const("key"),
        lambda rt: _const("log"),
        lambda rt: _const(after),
        lambda rt: _const(every),
    )


def _open(log: _Log, **schedule: object) -> object:
    rt = type("Rt", (), {"ctx": Context()})()
    return Stream(Literal(None), Literal(None))._acompile(0, _children(log, **schedule))(rt)


async def _take(agen: object, n: int) -> list:
    return [await asyncio.wait_for(agen.__anext__(), 5.0) for _ in range(n)]


async def test_stream_subscribes_before_the_first_drain() -> None:
    log = _Log(Feed(), ["a"])
    agen = await _open(log)
    assert await _take(agen, 1) == ["a"]
    assert log.order[:2] == ["subscribe", "advance"]
    await agen.aclose()


async def test_stream_does_not_miss_an_item_appended_as_the_catch_up_ends() -> None:
    """The write lands after the drain read the end and before a follow could subscribe.

    Under drain-then-subscribe nobody was listening yet, so the notification was
    lost and the item waited for some later write. Subscribing first means the
    write wakes another drain. No re-checks run, so only the notification can
    deliver it.
    """
    log = _Log(Feed(), ["a"])
    log.on_exhausted = lambda: log.append("b")
    agen = await _open(log)
    assert await _take(agen, 2) == ["a", "b"]
    await agen.aclose()


async def test_stream_follows_each_notification() -> None:
    log = _Log(Feed())
    agen = await _open(log)
    nxt = asyncio.ensure_future(agen.__anext__())
    await until(lambda: log.feed.receivers)
    log.append("x")
    assert await asyncio.wait_for(nxt, 5.0) == "x"
    log.append("y")
    log.append("z")
    assert await _take(agen, 2) == ["y", "z"]
    await agen.aclose()


async def test_stream_recheck_catches_a_dropped_notification() -> None:
    log = _Log(Feed())
    agen = await _open(log, after=(0.05,))
    nxt = asyncio.ensure_future(agen.__anext__())
    await until(lambda: log.feed.receivers)
    log.feed.dropping = 1
    log.append("lost")
    assert await asyncio.wait_for(nxt, 5.0) == "lost"
    await agen.aclose()


async def test_stream_close_unbinds_and_closes_the_subscription() -> None:
    log = _Log(Feed(), ["a"])
    agen = await _open(log, every=30.0)
    await _take(agen, 1)
    await agen.aclose()
    assert log.feed.log == ["bind", "unbind", "close"]
    assert live_rechecks() == []


async def test_stream_refuses_a_computed_schedule_before_subscribing() -> None:
    log = _Log(Feed(), ["a"])
    agen = await _open(log, every=-1.0)
    with pytest.raises(ValueError, match="Stream: every= must be positive"):
        await agen.__anext__()
    assert log.order == []


# ---------------------------------------------------------------------------
# Cursor scope: driven through the compiled thunk with hand-made children
# ---------------------------------------------------------------------------


class _Sub:
    """A change subscription that never fires."""

    def bind(self, receiver: object) -> None:
        pass

    def unbind(self, receiver: object) -> None:
        pass

    def close(self) -> None:
        pass


async def test_stream_cursor_lives_for_the_drain_only() -> None:
    ctx = Context()
    rt = type("Rt", (), {"ctx": ctx})()
    entries = iter([("log-1", "a"), ("log-2", "b")])
    seen: list = []

    async def advance(rt: object) -> object:
        return next(entries, None)

    async def change(rt: object) -> _Sub:
        return _Sub()

    async def body(rt: Runtime) -> object:
        seen.append((rt.ctx.attrs.get("key"), rt.ctx.attrs.get("log")))
        return [rt.ctx.attrs.get("key")]

    async def name(value: str) -> str:
        return value

    children = (
        advance,
        change,
        body,
        lambda rt: name("key"),
        lambda rt: name("log"),
        lambda rt: name(()),
        lambda rt: name(None),
    )
    agen = await Stream(Literal(None), Literal(None))._acompile(0, children)(rt)
    assert [await agen.__anext__(), await agen.__anext__()] == ["a", "b"]
    assert seen == [("a", "log-1"), ("b", "log-2")]  # advanced item by item
    assert ctx.attrs.get("log") == "log-2"  # still bound while the stream is open
    await agen.aclose()
    assert ctx.attrs.exists("log") is False  # gone once the stream is closed
    assert ctx.attrs.exists("key") is False
