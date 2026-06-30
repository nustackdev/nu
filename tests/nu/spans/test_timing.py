"""Tests for the timing policy spans - Timeout, Throttle, Debounce.

All three are async-only: the sync entry is refused. Timeout bounds the body and
runs on_timeout (live ctx) or raises; Throttle drops calls inside the interval
(state in attrs); Debounce schedules the body and cancels a pending run on
re-entry.
"""

from __future__ import annotations

import asyncio

import pytest
from _support.policy_atoms import CountAction, RecordAction, SlowAction

from nu.context import AttrRef, SetCommand
from nu.core import LiteralQuery
from nu.lang import Policy, Span
from nu.lang.helpers import arun, run
from nu.lang.runtime.context.context import Context
from nu.spans import Debounce, Throttle, Timeout


def _set(name: str, value: object) -> SetCommand:
    return SetCommand(AttrRef(name), LiteralQuery(value))


# --- basis ----------------------------------------------------------------


def test_timing_spans_are_policy_spans() -> None:
    for kind in (Timeout, Throttle, Debounce):
        assert issubclass(kind, Policy)
        assert issubclass(kind, Span)


# --- Timeout --------------------------------------------------------------


def test_timeout_refuses_sync_run() -> None:
    with pytest.raises(RuntimeError):
        run(Timeout(1.0, SlowAction(0.0)))


async def test_timeout_within_limit_forwards_the_value() -> None:
    value, ctx = await arun(Timeout(1.0, SlowAction(0.0, "x")))
    assert value == "x"
    assert ctx.attrs["x"] is True


async def test_timeout_exceeded_without_handler_raises() -> None:
    with pytest.raises(TimeoutError):
        await arun(Timeout(0.01, SlowAction(1.0)))


async def test_timeout_exceeded_runs_on_timeout_on_the_live_ctx() -> None:
    value, ctx = await arun(Timeout(0.01, SlowAction(1.0), on_timeout=_set("timed_out", True)))
    assert value is None
    assert ctx.attrs["timed_out"] is True


# --- Throttle -------------------------------------------------------------


def test_throttle_refuses_sync_run() -> None:
    with pytest.raises(RuntimeError):
        run(Throttle(1.0, CountAction()))


async def test_throttle_drops_a_second_call_inside_the_interval() -> None:
    ctx = Context()
    tree = Throttle(10.0, CountAction())
    await arun(tree, ctx)
    await arun(tree, ctx)
    assert ctx.attrs["count"] == 1  # second call dropped


# --- Debounce -------------------------------------------------------------


def test_debounce_refuses_sync_run() -> None:
    with pytest.raises(RuntimeError):
        run(Debounce(0.01, CountAction()))


async def test_debounce_fires_after_the_delay() -> None:
    log: list = []
    ctx = Context()
    await arun(Debounce(0.01, RecordAction(log, "f")), ctx)
    assert log == []  # not yet
    await asyncio.sleep(0.05)
    assert len(log) == 1


async def test_debounce_reentry_cancels_the_pending_run() -> None:
    log: list = []
    ctx = Context()
    tree = Debounce(0.03, RecordAction(log, "f"))
    await arun(tree, ctx)
    await arun(tree, ctx)  # cancels the first pending run
    await asyncio.sleep(0.08)
    assert len(log) == 1  # only the last run fired
