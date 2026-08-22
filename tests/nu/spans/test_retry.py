"""Tests for the Retry policy span - full v1 parity.

Sync is a basic retry (max_attempts + errors); async adds delay/backoff/jitter
and the on_attempt_fail / on_success / on_fail hooks (each against an isolated
ctx copy carrying attempt + error). A stream body is retried by atomic
re-evaluation.
"""

from __future__ import annotations

import pytest
from _support.policy_atoms import FlakyAction, FlakyStream, RecordAction

from nu.core import Literal
from nu.lang import Attr, Cardinality, Policy, Span
from nu.lang.helpers import acollect, arun, collect, compile, run
from nu.spans import Retry


# --- basis ----------------------------------------------------------------


def test_retry_is_a_policy_span() -> None:
    assert issubclass(Retry, Policy)
    assert issubclass(Retry, Span)
    program = compile(Retry(Literal(5)))
    assert program.attr(program.root, Attr.CHILD_CARDINALITY) is Cardinality.SCALAR


# --- sync: basic retry ----------------------------------------------------


def test_sync_success_first_try() -> None:
    value, _ = run(Retry(Literal(5)))
    assert value == 5


def test_sync_retries_then_succeeds() -> None:
    value, ctx = run(Retry(FlakyAction(1), max_attempts=3))
    assert value == "flaky"
    assert ctx.attrs["__flaky_calls_flaky__"] == 2  # failed once, then succeeded


def test_sync_exhausts_attempts_and_raises() -> None:
    with pytest.raises(ValueError, match="flaky"):
        run(Retry(FlakyAction(5), max_attempts=2))


def test_sync_error_outside_filter_propagates_unretried() -> None:
    with pytest.raises(ValueError, match="flaky"):
        run(Retry(FlakyAction(5), max_attempts=3, errors=KeyError))


# --- async: full policy ---------------------------------------------------


async def test_async_retries_then_succeeds() -> None:
    value, _ = await arun(Retry(FlakyAction(1), max_attempts=3))
    assert value == "flaky"


async def test_async_on_success_hook_fires_with_attempt() -> None:
    log: list = []
    await arun(Retry(FlakyAction(0), max_attempts=3, on_success=RecordAction(log, "ok")))
    assert log == [("ok", 1, None)]


async def test_async_attempt_fail_and_fail_hooks_fire() -> None:
    log: list = []
    value, _ = await arun(
        Retry(
            FlakyAction(5),
            max_attempts=2,
            on_attempt_fail=RecordAction(log, "af"),
            on_fail=RecordAction(log, "fail"),
        ),
    )
    assert value is None  # on_fail present -> swallow, return None
    tags = [entry[0] for entry in log]
    assert tags == ["af", "fail"]
    assert log[-1][2] is not None  # error string was set for the fail hook


async def test_async_exhausts_without_on_fail_raises() -> None:
    with pytest.raises(ValueError, match="flaky"):
        await arun(Retry(FlakyAction(5), max_attempts=2))


# --- stream body: atomic re-evaluation ------------------------------------


def test_sync_stream_retries_fresh_each_attempt() -> None:
    items, _ = collect(compile(Retry(FlakyStream(1, [1, 2, 3]), max_attempts=3)))
    assert items == [1, 2, 3]


async def test_async_stream_retries_fresh_each_attempt() -> None:
    items, _ = await acollect(compile(Retry(FlakyStream(1, [1, 2]), max_attempts=3)))
    assert items == [1, 2]
