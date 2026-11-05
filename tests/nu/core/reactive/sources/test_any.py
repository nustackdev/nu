"""Tests for OnAny: one subscription over several.

Members are hand-fired ``Feed`` subscriptions read from ctx attrs, so each test
decides which member fires and with which key.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest
from _support.reactive import Body, Feed, Read, start, stop, until

import nu
from nu.context import Attr as AttrRef
from nu.core.reactive.event import ReactEvery
from nu.core.reactive.level import Reconcile
from nu.core.reactive.protocol import Subscription
from nu.core.reactive.sources.any import OnAny
from nu.lang import Context, ScalarQuery
from nu.lang.helpers import arun


if TYPE_CHECKING:
    from nu.lang.runtime import Runtime


def _feeds(*names: str) -> dict[str, Feed]:
    return {name: Feed() for name in names}


async def _open(term: object, feeds: dict[str, Feed]) -> Subscription:
    sub, _ = await arun(term, Context(attrs=dict(feeds)))
    return sub


# ---------------------------------------------------------------------------
# Construction and the sync path
# ---------------------------------------------------------------------------


def test_on_any_is_a_scalar_query():
    assert issubclass(OnAny, ScalarQuery)
    assert nu.OnAny is OnAny


def test_on_any_with_no_member_raises_at_build():
    with pytest.raises(TypeError, match="OnAny needs at least one subscription"):
        OnAny()


def test_on_any_sync_thunk_raises():
    thunk = OnAny(AttrRef("a"))._compile(0, ())
    with pytest.raises(RuntimeError, match="OnAny requires an async runtime; use arun"):
        thunk(None)


# ---------------------------------------------------------------------------
# One subscription over every member
# ---------------------------------------------------------------------------


async def test_on_any_yields_one_subscription_over_every_member():
    feeds = _feeds("a", "b")
    sub = await _open(OnAny(AttrRef("a"), AttrRef("b")), feeds)
    assert isinstance(sub, Subscription)
    heard: list = []
    sub.bind(heard.append)
    feeds["a"].fire("ka")
    feeds["b"].fire("kb")
    feeds["b"].fire(None)
    assert heard == ["ka", "kb", None]  # each member's own key, None included
    sub.unbind(heard.append)
    feeds["a"].fire("late")
    assert heard == ["ka", "kb", None]
    sub.close()
    for feed in feeds.values():
        assert feed.log == ["bind", "unbind", "close"]


async def test_on_any_closes_every_member_even_when_one_raises():
    class _Broken(Feed):
        def close(self) -> None:
            super().close()
            msg = "broken close"
            raise OSError(msg)

    feeds = {"a": _Broken(), "b": Feed()}
    sub = await _open(OnAny(AttrRef("a"), AttrRef("b")), feeds)
    with pytest.raises(OSError, match="broken close"):
        sub.close()
    assert feeds["a"].closed
    assert feeds["b"].closed


async def test_on_any_closes_the_opened_members_when_a_later_one_fails():
    async def fail(rt: Runtime) -> object:
        msg = "cannot open"
        raise ConnectionError(msg)

    feeds = _feeds("a")
    with pytest.raises(ConnectionError, match="cannot open"):
        await _open(OnAny(AttrRef("a"), Read(fail)), feeds)
    assert feeds["a"].log == ["close"]


class _BrokenClose(Feed):
    def close(self) -> None:
        super().close()
        msg = "broken close"
        raise OSError(msg)


async def test_on_any_open_failure_survives_a_member_that_fails_to_close():
    async def fail(rt: Runtime) -> object:
        msg = "cannot open"
        raise ConnectionError(msg)

    feeds = {"a": _BrokenClose(), "b": Feed()}
    with pytest.raises(ConnectionError, match="cannot open"):
        await _open(OnAny(AttrRef("a"), AttrRef("b"), Read(fail)), feeds)
    assert feeds["a"].closed
    assert feeds["b"].closed


async def test_on_any_cancelled_open_survives_a_member_that_fails_to_close():
    opening = asyncio.Event()

    async def hang(rt: Runtime) -> object:
        opening.set()
        await asyncio.Event().wait()

    feeds = {"a": _BrokenClose()}
    task = asyncio.create_task(_open(OnAny(AttrRef("a"), Read(hang)), feeds))
    await opening.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert feeds["a"].closed


async def test_on_any_bind_failure_unbinds_the_members_already_bound():
    class _NoBind(Feed):
        def bind(self, receiver: object) -> None:
            msg = "cannot bind"
            raise OSError(msg)

    feeds = {"a": Feed(), "b": _NoBind()}
    sub = await _open(OnAny(AttrRef("a"), AttrRef("b")), feeds)
    with pytest.raises(OSError, match="cannot bind"):
        sub.bind(print)
    assert feeds["a"].log == ["bind", "unbind"]
    assert feeds["a"].receivers == []


# ---------------------------------------------------------------------------
# Laws: OnAny(a) = a, and nesting flattens
# ---------------------------------------------------------------------------


def _recorder(log: list) -> Body:
    async def body(rt: Runtime) -> None:
        log.append(rt.ctx.attrs.get("k"))

    return Body(body)


async def _deliveries(change: object, fires: list[tuple[str, object]], names: tuple) -> tuple:
    """What a ReactEvery over ``change`` hears for ``fires``, and each member's lifecycle."""
    feeds, seen = _feeds(*names), []
    task = start(ReactEvery(change, _recorder(seen), changed_key="k"), **feeds)
    await until(lambda: all(feed.receivers for feed in feeds.values()))
    for name, key in fires:
        feeds[name].fire(key)
    await until(lambda: len(seen) == len(fires))
    await stop(task)
    return seen, {name: feed.log for name, feed in feeds.items()}


async def test_law_on_any_of_one_behaves_as_the_member():
    fires = [("a", 1), ("a", None), ("a", "x")]
    alone = await _deliveries(AttrRef("a"), fires, ("a",))
    wrapped = await _deliveries(OnAny(AttrRef("a")), fires, ("a",))
    assert wrapped == alone
    assert alone[0] == [1, None, "x"]


async def test_law_on_any_nests():
    fires = [("a", 1), ("c", 2), ("b", None), ("c", 3), ("a", 4)]
    names = ("a", "b", "c")
    flat = await _deliveries(OnAny(AttrRef("a"), AttrRef("b"), AttrRef("c")), fires, names)
    nested = await _deliveries(OnAny(AttrRef("a"), OnAny(AttrRef("b"), AttrRef("c"))), fires, names)
    left = await _deliveries(OnAny(OnAny(AttrRef("a"), AttrRef("b")), AttrRef("c")), fires, names)
    assert nested == flat == left
    assert flat[0] == [1, 2, None, 3, 4]
    assert flat[1] == {name: ["bind", "unbind", "close"] for name in names}


# ---------------------------------------------------------------------------
# In a level flow: any member wakes a pass
# ---------------------------------------------------------------------------


async def test_on_any_wakes_a_level_flow_from_any_member():
    feeds, passes = _feeds("a", "b"), []

    async def body(rt: Runtime) -> None:
        passes.append(len(passes))

    task = start(
        Reconcile(OnAny(AttrRef("a"), AttrRef("b")), Body(body), after=(), every=None), **feeds
    )
    await until(lambda: len(passes) == 1)  # the pass right after subscribing
    feeds["b"].fire("kb")
    await until(lambda: len(passes) == 2)
    feeds["a"].fire("ka")
    await until(lambda: len(passes) == 3)
    await stop(task)
    for feed in feeds.values():
        assert feed.log == ["bind", "unbind", "close"]
