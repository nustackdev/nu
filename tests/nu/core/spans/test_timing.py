"""Tests for the timing policy span Timeout.

Async-only: the sync entry is refused. Timeout bounds the body and runs
on_timeout (live ctx) or raises.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest
from _support.attrs import declared
from _support.policy_atoms import SlowAction

import nu
from nu.core.spans import Timeout
from nu.lang import Literal, Policy, Span
from nu.lang.helpers import arun, run


if TYPE_CHECKING:
    from nu.domains.shape.interactions import SetCmd


class S(nu.Shape):
    """The mem slot the timeout handler writes."""

    timed_out = nu.mem.ObjectRef.slot()


def _set(name: str, value: object) -> SetCmd:
    return getattr(S, name).set(Literal(value))


# --- basis ----------------------------------------------------------------


def test_timing_spans_are_policy_spans() -> None:
    assert issubclass(Timeout, Policy)
    assert issubclass(Timeout, Span)


# --- Timeout --------------------------------------------------------------


def test_timeout_refuses_sync_run() -> None:
    with pytest.raises(RuntimeError):
        run(Timeout(1.0, SlowAction(0.0)))


async def test_timeout_within_limit_forwards_the_value() -> None:
    value, ctx = await arun(Timeout(1.0, SlowAction(0.0, "x")), declared("x"))
    assert value == "x"
    assert ctx.attrs.get("x") is True


async def test_timeout_exceeded_without_handler_raises() -> None:
    with pytest.raises(TimeoutError):
        await arun(Timeout(0.01, SlowAction(1.0)))


async def test_timeout_exceeded_runs_on_timeout_on_the_live_ctx() -> None:
    data: dict = {}
    value, _ = await arun(
        Timeout(0.01, SlowAction(1.0), on_timeout=_set("timed_out", True)),
        declared("slow").bind(dict, data, S),
    )
    assert value is None
    assert data["timed_out"] is True


async def test_timeout_keeps_a_cancel_that_lands_as_the_body_finishes() -> None:
    flow = Timeout(10.0, SlowAction(0.0)) >> SlowAction(0.05, "after")
    for steps in range(1, 6):
        task = asyncio.ensure_future(arun(flow, declared("slow", "after")))
        for _ in range(steps):
            await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
