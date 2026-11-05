"""The laws that span more than one reactive flow, each run against every flow it names.

Two laws live here:

- An arm error propagates out of ``ReconcileLatestEach``, ``ReconcileLatest``,
  ``ReactLatestEach``, ``ReactEach`` and ``ReconcileEach``: the running
  siblings are cancelled and drained, then the subscription is let go.
- An arm runs once per appearance of its id: a finished arm of
  ``ReconcileLatestEach`` or ``ReconcileLatest`` is not started again while
  its id stays, and is born again after the id leaves and returns.

The laws about one flow sit next to that flow's tests:

- ``OnAny(a)`` behaves as ``a``, and ``OnAny`` nests: ``sources/test_any.py``.
- ``Race(x, Park())`` behaves as ``x``: ``tests/nu/core/flows/test_control.py``.
- ``ReconcileLatestEach([], c, f)`` runs nothing and never returns:
  ``level/test_latest_each.py``.
- ``ReconcileLatest(const v, c, f)`` runs ``f(v)`` once and then holds:
  ``level/test_latest.py``.
- ``WaitUntil(c, True)`` returns at once (``level/test_wait.py``), and
  ``WaitUntil(c, x)`` agrees with ``ReconcileWhile(c, Not(x), Noop())``
  (``level/test_while.py``).
- Every event flow runs its body for a ``None`` key: ``event/test_keys.py``.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest
from _support.reactive import QUIET, Body, Feed, Read, settle_loop, start, stop, until

from nu.context import Attr as AttrRef
from nu.core.reactive import (
    ReactEach,
    ReactLatestEach,
    ReconcileEach,
    ReconcileLatest,
    ReconcileLatestEach,
)


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


# ---------------------------------------------------------------------------
# An arm error propagates; the siblings are cancelled and drained first
# ---------------------------------------------------------------------------


def _arm(log: list, ready: asyncio.Event) -> Body:
    """``a`` parks until cancelled; ``boom`` waits for ``a`` to be running, then raises."""

    async def body(rt: Runtime) -> None:
        x = rt.ctx.attrs.get("x")
        if x == "boom":
            await ready.wait()
            msg = "boom"
            raise ValueError(msg)
        log.append(("start", x))
        ready.set()
        try:
            await asyncio.Event().wait()
        finally:
            log.append(("end", x))

    return Body(body)


def _ids(state: dict) -> Read:
    async def read(rt: Runtime) -> object:
        return state["ids"]

    return Read(read)


async def _fire_both(feed: Feed, state: dict, log: list) -> None:
    """Event flows: notify ``a``, then ``boom`` once ``a`` runs."""
    await until(lambda: feed.receivers)
    feed.fire("a")
    await until(lambda: ("start", "a") in log)
    feed.fire("boom")


async def _read_both(feed: Feed, state: dict, log: list) -> None:
    """Level flows over many ids: both ids are in the first read."""


async def _switch_to_boom(feed: Feed, state: dict, log: list) -> None:
    """``ReconcileLatest``: the one id moves from ``a`` to ``boom``."""
    await until(lambda: ("start", "a") in log)
    state["ids"] = "boom"
    feed.fire()


_ERROR_CASES = [
    pytest.param(
        lambda s, b: ReconcileLatestEach(_ids(s), AttrRef("feed"), b, "x", **QUIET),
        ["a", "boom"],
        _read_both,
        id="ReconcileLatestEach",
    ),
    pytest.param(
        lambda s, b: ReconcileEach(_ids(s), AttrRef("feed"), b, "x", **QUIET),
        ["a", "boom"],
        _read_both,
        id="ReconcileEach",
    ),
    pytest.param(
        lambda s, b: ReconcileLatest(_ids(s), AttrRef("feed"), b, "x", **QUIET),
        "a",
        _switch_to_boom,
        id="ReconcileLatest",
    ),
    pytest.param(
        lambda s, b: ReactEach(AttrRef("feed"), b, changed_key="x"),
        None,
        _fire_both,
        id="ReactEach",
    ),
    pytest.param(
        lambda s, b: ReactLatestEach(AttrRef("feed"), b, changed_key="x"),
        None,
        _fire_both,
        id="ReactLatestEach",
    ),
]


@pytest.mark.parametrize(("make", "ids", "drive"), _ERROR_CASES)
async def test_an_arm_error_propagates_after_the_siblings_are_drained(
    make: Callable, ids: object, drive: Callable
) -> None:
    log: list = []
    feed, state, ready = Feed(log), {"ids": ids}, asyncio.Event()
    task = start(make(state, _arm(log, ready)), feed=feed)
    await drive(feed, state, log)
    with pytest.raises(ValueError, match="boom"):
        await asyncio.wait_for(task, 5)
    # The running sibling was cancelled and fully unwound before the flow let go.
    assert log.index(("end", "a")) < log.index("unbind")
    assert log[-2:] == ["unbind", "close"]
    assert feed.receivers == []


# ---------------------------------------------------------------------------
# An arm runs once per appearance of its id
# ---------------------------------------------------------------------------


def _finishing(log: list) -> Body:
    async def body(rt: Runtime) -> None:
        log.append(("start", rt.ctx.attrs.get("x")))

    return Body(body)


_ONCE_CASES = [
    pytest.param(
        lambda s, b: ReconcileLatestEach(_ids(s), AttrRef("feed"), b, "x", **QUIET),
        ["a"],
        [],
        id="ReconcileLatestEach",
    ),
    pytest.param(
        lambda s, b: ReconcileLatest(_ids(s), AttrRef("feed"), b, "x", **QUIET),
        "a",
        None,
        id="ReconcileLatest",
    ),
]


@pytest.mark.parametrize(("make", "present", "absent"), _ONCE_CASES)
async def test_a_finished_arm_stays_finished_until_its_id_leaves_and_returns(
    make: Callable, present: object, absent: object
) -> None:
    log: list = []
    feed, state = Feed(), {"ids": present}
    task = start(make(state, _finishing(log)), feed=feed)
    await until(lambda: log == [("start", "a")])
    for _ in range(3):
        feed.fire()
        await settle_loop()
    assert log == [("start", "a")]
    state["ids"] = absent
    feed.fire()
    await settle_loop()
    state["ids"] = present
    feed.fire()
    await until(lambda: log == [("start", "a"), ("start", "a")])
    await stop(task)
