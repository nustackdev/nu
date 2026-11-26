"""Tests every event flow shares: each notification reaches the body, ``None`` included.

The two flows that key by notification (``ReactEach``, ``ReactLatestEach``)
share two more: the lambda body form over the key, and a clear error on a
key that cannot be one.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest
from _support.policy_atoms import Sink
from _support.reactive import FEED, Body, Feed, start, stop, until

import nu
from nu.core.reactive.event import (
    ReactEach,
    ReactEvery,
    ReactLatest,
    ReactLatestEach,
    ReactOnce,
    ReactWhile,
)
from nu.engine.structure import Declared
from nu.lang import ScalarAction


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


# ---------------------------------------------------------------------------
# Every notification reaches the body, None included
# ---------------------------------------------------------------------------


def _keyed(log: list) -> Callable:
    async def body(rt: Runtime, k: object) -> None:
        log.append(k)

    return lambda k: Body(body, k)


@pytest.mark.parametrize(
    "make",
    [
        lambda log: ReactOnce(FEED, _keyed(log)),
        lambda log: ReactEvery(FEED, _keyed(log)),
        lambda log: ReactLatest(FEED, _keyed(log)),
        lambda log: ReactWhile(FEED, nu.Literal(True), _keyed(log)),
        lambda log: ReactEach(FEED, _keyed(log)),
        lambda log: ReactLatestEach(FEED, _keyed(log)),
    ],
    ids=["ReactOnce", "ReactEvery", "ReactLatest", "ReactWhile", "ReactEach", "ReactLatestEach"],
)
async def test_event_flows_fire_on_a_notify_without_payload(make: Callable) -> None:
    """A ``None`` key is a real notification (a ui notify carries no payload)."""
    feed, log = Feed(), []
    task = start(make(log), feed=feed)
    await until(lambda: feed.receivers)
    feed.fire(None)
    await until(lambda: log == [None])
    if task.done():
        await task
    else:
        await stop(task)


# ---------------------------------------------------------------------------
# The keyed flows: a lambda over the key, and a key that cannot be one
# ---------------------------------------------------------------------------


class _Record(ScalarAction):
    """Appends its child's value to ``log``: the body a lambda builds over the key."""

    _requires_async = Declared(value=True, name="requires_async")
    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(self, value: object, log: list) -> None:
        super().__init__(value, Sink(log))

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            msg = "_Record was placed on the sync path"
            raise RuntimeError(msg)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        value, sink = children

        async def athunk(rt: Runtime) -> None:
            (await sink(rt)).append(await value(rt))

        return athunk


_KEYED = pytest.mark.parametrize(
    "flow", [ReactEach, ReactLatestEach], ids=["ReactEach", "ReactLatestEach"]
)


@_KEYED
async def test_keyed_flows_take_a_lambda_over_the_key(flow: type) -> None:
    """The lambda body over the key: the body it builds sees every key."""
    feed, log = Feed(), []
    task = start(flow(FEED, lambda key: _Record(key, log)), feed=feed)
    await until(lambda: feed.receivers)
    feed.fire("a")
    feed.fire("b")
    await until(lambda: sorted(log) == ["a", "b"])
    await stop(task)


@_KEYED
async def test_keyed_flows_refuse_an_unhashable_key_naming_themselves(flow: type) -> None:
    feed = Feed()
    task = start(flow(FEED, nu.Noop()), feed=feed)
    await until(lambda: feed.receivers)
    feed.fire([1])
    with pytest.raises(TypeError, match=rf"{flow.__name__}: ids must be hashable, got list"):
        await asyncio.wait_for(task, 5)
    assert feed.log == ["bind", "unbind", "close"]
