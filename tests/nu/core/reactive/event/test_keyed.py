"""Tests for the per-key serial queues behind ReactEach, driven without a flow."""

from __future__ import annotations

import asyncio

import pytest
from _support.reactive import settle_loop, until

from nu.core.reactive.event._keyed import KeyedQueues


def _runner(log: list, holds: list) -> object:
    """A run that logs its start, parks on a fresh gate the test releases, then logs its end."""

    async def run(key: object) -> None:
        log.append(("start", key))
        gate = asyncio.Event()
        holds.append(gate)
        await gate.wait()
        log.append(("end", key))

    return run


async def test_keyed_runs_one_key_in_order() -> None:
    log, holds = [], []
    queues = KeyedQueues(_runner(log, holds))
    await queues.put("a")
    await queues.put("a")
    await until(lambda: log == [("start", "a")])
    await asyncio.sleep(0.01)
    assert log == [("start", "a")]
    holds[0].set()
    await until(lambda: len(log) == 3)
    assert log == [("start", "a"), ("end", "a"), ("start", "a")]
    holds[1].set()
    await until(lambda: len(log) == 4)
    await queues.drain()


async def test_keyed_runs_keys_side_by_side() -> None:
    log, holds = [], []
    queues = KeyedQueues(_runner(log, holds))
    await queues.put("a")
    await queues.put("b")
    await until(lambda: len(log) == 2)
    assert log == [("start", "a"), ("start", "b")]
    assert set(queues.book.arms) == {"a", "b"}
    await queues.drain()


async def test_keyed_worker_leaves_when_its_backlog_drains() -> None:
    log, holds = [], []
    queues = KeyedQueues(_runner(log, holds))
    await queues.put("a")
    await until(lambda: holds)
    holds[0].set()
    await until(lambda: ("end", "a") in log)
    await settle_loop()
    assert queues.book.arms == {}
    assert queues.backlogs == {}
    # The next notification starts a fresh worker for the key.
    await queues.put("a")
    await until(lambda: len(holds) == 2)
    assert "a" in queues.book.arms
    await queues.drain()


async def test_keyed_put_on_the_tick_a_worker_returns_births_a_fresh_one() -> None:
    runs: list = []

    async def run(key: object) -> None:
        runs.append(key)

    queues = KeyedQueues(run)
    await queues.put("a")
    first = queues.book.arms["a"]
    await asyncio.sleep(0)  # the worker runs its one notification and returns
    assert first.done()
    assert queues.book.arms["a"] is first  # its done callback has not landed yet
    assert queues.backlogs == {}
    await queues.put("a")
    # The sweep settled the finished worker and a fresh one took the key.
    assert queues.book.arms["a"] is not first
    await until(lambda: runs == ["a", "a"])
    await settle_loop()
    assert queues.book.arms == {}
    assert queues.backlogs == {}
    await queues.drain()


async def test_keyed_unhashable_key_is_a_clear_error_naming_the_owner() -> None:
    queues = KeyedQueues(_runner([], []), owner="Flow")
    with pytest.raises(TypeError, match=r"Flow: ids must be hashable, got list \[1\]"):
        await queues.put([1])
    assert queues.book.arms == {}
    assert queues.backlogs == {}


async def test_keyed_worker_error_surfaces_on_wait_and_put() -> None:
    async def run(key: object) -> None:
        msg = f"boom {key}"
        raise ValueError(msg)

    queues = KeyedQueues(run, owner="Flow")
    await queues.put("a")
    with pytest.raises(ValueError, match="boom a"):
        await queues.wait(asyncio.Event().wait())
    assert queues.book.arms == {}
    assert queues.backlogs == {}
    with pytest.raises(ValueError, match="boom a"):
        await queues.put("b")
    await queues.drain()


async def test_keyed_drain_cancels_every_worker_and_drops_backlogs() -> None:
    log, holds = [], []
    queues = KeyedQueues(_runner(log, holds))
    for key in ("a", "a", "b"):
        await queues.put(key)
    await until(lambda: len(log) == 2)
    await queues.drain()
    assert queues.book.arms == {}
    assert queues.backlogs == {}
    assert ("end", "a") not in log
    assert len(log) == 2
