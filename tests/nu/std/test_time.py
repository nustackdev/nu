"""Functional tests for ``nu.std.time`` - drive the Forms through the engine.

Clock reads are non-deterministic, so assertions are property-based: types,
non-negativity, monotonicity. ``sleep`` is checked for its effect (elapsed time)
and its VOID yield. One structural test pins ``sleep`` as sync-only.
"""

from __future__ import annotations

import asyncio
import time as _time

from nu.lang import compile
from nu.lang.helpers import arun, run
from nu.std.time import (
    monotonic,
    monotonic_ns,
    perf_counter,
    perf_counter_ns,
    process_time,
    sleep,
    time,
    time_ns,
)


def test_time_returns_positive_float() -> None:
    value, _ = run(time())
    assert isinstance(value, float)
    assert value > 0.0


def test_monotonic_returns_float() -> None:
    value, _ = run(monotonic())
    assert isinstance(value, float)


def test_perf_counter_returns_float() -> None:
    value, _ = run(perf_counter())
    assert isinstance(value, float)


def test_process_time_returns_float() -> None:
    value, _ = run(process_time())
    assert isinstance(value, float)


def test_ns_reads_return_ints() -> None:
    for term in (time_ns(), monotonic_ns(), perf_counter_ns()):
        value, _ = run(term)
        assert isinstance(value, int)
        assert value > 0


def test_monotonic_is_non_decreasing() -> None:
    first, _ = run(monotonic())
    second, _ = run(monotonic())
    assert second >= first


def test_sleep_yields_none_and_elapses() -> None:
    start = _time.monotonic()
    value, _ = run(sleep(0.05))
    elapsed = _time.monotonic() - start
    assert value is None
    assert elapsed >= 0.04


def test_sleep_runs_on_async_path() -> None:
    value, _ = asyncio.run(arun(sleep(0.01)))
    assert value is None


def test_sleep_is_sync_only() -> None:
    # time.sleep blocks the loop, so its atom has no async affinity.
    program = compile(sleep(0.0))
    assert program.attr((0,), "async_affinity") is False
