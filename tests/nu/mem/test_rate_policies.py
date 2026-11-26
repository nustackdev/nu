"""``nu.mem.Throttle`` and ``nu.mem.Debounce``: rate policies with their state in mem.

Both only mean something across calls, so most tests run them in a loop and put
the frame holding their ref around it. One test per policy puts the frame
inside the loop instead, to pin that the state lasts exactly as long as the
frame that holds it.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
import nu.mem as nm


class Rate(nu.Shape):
    last = nm.FloatRef.slot()
    other = nm.FloatRef.slot()
    pending = nm.ObjectRef.slot()


class Out(nu.Shape):
    log = nm.ListRef.slot(int)


def _arun(term: nu.Nu) -> list[int]:
    """Run ``term`` async against a fresh ``Out`` log; return what it logged."""
    data: dict = {"log": []}
    asyncio.run(nu.arun(term, nu.Context().bind(dict, data, Out)))
    return data["log"]


def _ran(n: int = 1) -> nu.Nu:
    return Out.log.append(n)


# --- Throttle --------------------------------------------------------------------


def test_throttle_runs_the_first_call_and_yields_its_value() -> None:
    term = nm.let(Rate, nm.Throttle(60.0, nu.Add(1, 2), last=Rate.last))
    assert asyncio.run(nu.arun(term))[0] == 3


def test_throttle_drops_a_call_inside_the_interval() -> None:
    once = nm.Throttle(60.0, _ran(), last=Rate.last)
    assert _arun(nm.let(Rate, nu.ForEachDo(nu.Iter([1, 2, 3]), once))) == [1]


def test_throttle_reads_none_as_never_run() -> None:
    loop = nm.let(
        lambda last: nu.ForEachDo(nu.Iter([1, 2, 3]), nm.Throttle(60.0, _ran(), last=last)),
        last=None,
    )
    assert _arun(loop) == [1]


def test_throttle_runs_again_once_the_interval_passed() -> None:
    once = nm.Throttle(0.02, _ran(), last=Rate.last)
    assert _arun(nm.let(Rate, once >> nu.Delay(0.05) >> once)) == [1, 1]


def test_throttle_state_persists_across_a_forever_loop() -> None:
    tick = nm.Throttle(0.1, _ran(), last=Rate.last)
    loop = nu.Race(nu.ForeverDo(nu.DelayedDo(0.01, tick)), nu.Delay(0.25))
    runs = _arun(nm.let(Rate, loop))
    assert 1 <= len(runs) <= 3


def test_throttle_state_ends_with_its_frame() -> None:
    once = nm.Throttle(60.0, _ran(), last=Rate.last)
    assert _arun(nu.ForEachDo(nu.Iter([1, 2, 3]), nm.let(Rate, once))) == [1, 1, 1]


def test_throttles_on_different_refs_are_independent() -> None:
    a = nm.Throttle(60.0, _ran(1), last=Rate.last)
    b = nm.Throttle(60.0, _ran(2), last=Rate.other)
    assert _arun(nm.let(Rate, a >> b >> a >> b)) == [1, 2]


def test_throttle_refuses_the_sync_runner() -> None:
    with pytest.raises(Exception, match="async"):
        nu.run(nm.let(Rate, nm.Throttle(1.0, nu.Add(1, 2), last=Rate.last)))


# --- Debounce --------------------------------------------------------------------


def test_debounce_yields_none_at_once() -> None:
    term = nm.let(Rate, nm.Debounce(0.01, nu.Add(1, 2), pending=Rate.pending))
    assert asyncio.run(nu.arun(term))[0] is None


def test_debounce_fires_once_for_a_burst() -> None:
    call = nm.Debounce(0.02, _ran(), pending=Rate.pending)
    burst = nu.ForEachDo(nu.Iter([1, 2, 3]), call) >> nu.Delay(0.1)
    assert _arun(nm.let(Rate, burst)) == [1]


def test_debounce_fires_each_call_spaced_past_the_delay() -> None:
    call = nm.Debounce(0.01, _ran(), pending=Rate.pending)
    assert _arun(nm.let(Rate, call >> nu.Delay(0.05) >> call >> nu.Delay(0.05))) == [1, 1]


def test_debounce_state_persists_across_a_forever_loop() -> None:
    call = nm.Debounce(0.05, _ran(), pending=Rate.pending)
    loop = nu.Race(nu.ForeverDo(nu.DelayedDo(0.01, call)), nu.Delay(0.2))
    assert _arun(nm.let(Rate, loop >> nu.Delay(0.1))) == [1]


def test_debounce_refuses_the_sync_runner() -> None:
    with pytest.raises(Exception, match="async"):
        nu.run(nm.let(Rate, nm.Debounce(0.01, nu.Add(1, 2), pending=Rate.pending)))


def test_a_debounced_body_reads_its_frame_after_the_frame_exited() -> None:
    # The delayed body holds the Runtime it was scheduled on, so the frames it
    # reads stay alive after both lets have exited, when it fires.
    call = lambda n: nm.let(Rate, nm.Debounce(0.01, Out.log.append(n), pending=Rate.pending))  # noqa: E731
    assert _arun(nm.let(call, n=7) >> nu.Delay(0.05)) == [7]


def test_a_debounced_loop_body_reads_the_item_of_the_call_that_fired() -> None:
    # Each body run has a frame of its own: the one run that fires, after the
    # loop has ended, is the burst's last call and reads that call's item.
    call = lambda item: nm.Debounce(0.02, Out.log.append(item), pending=Rate.pending)  # noqa: E731
    burst = nu.ForEachDo(nu.Iter([1, 2, 3]), call) >> nu.Delay(0.1)
    assert _arun(nm.let(Rate, burst)) == [3]
