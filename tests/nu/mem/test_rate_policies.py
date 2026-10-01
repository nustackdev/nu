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
    term = nm.Frame(Rate, nm.Throttle(60.0, nu.Add(1, 2), last=Rate.last))
    assert asyncio.run(nu.arun(term))[0] == 3


def test_throttle_drops_a_call_inside_the_interval() -> None:
    once = nm.Throttle(60.0, _ran(), last=Rate.last)
    assert _arun(nm.Frame(Rate, nu.ForEachDo(nu.Iter([1, 2, 3]), once))) == [1]


def test_throttle_reads_none_as_never_run() -> None:
    loop = nm.let(
        None, lambda last: nu.ForEachDo(nu.Iter([1, 2, 3]), nm.Throttle(60.0, _ran(), last=last))
    )
    assert _arun(loop) == [1]


def test_throttle_runs_again_once_the_interval_passed() -> None:
    once = nm.Throttle(0.02, _ran(), last=Rate.last)
    assert _arun(nm.Frame(Rate, once >> nu.Delay(0.05) >> once)) == [1, 1]


def test_throttle_state_persists_across_a_forever_loop() -> None:
    tick = nm.Throttle(0.1, _ran(), last=Rate.last)
    loop = nu.Race(nu.ForeverDo(nu.DelayedDo(0.01, tick)), nu.Delay(0.25))
    runs = _arun(nm.Frame(Rate, loop))
    assert 1 <= len(runs) <= 3


def test_throttle_state_ends_with_its_frame() -> None:
    once = nm.Throttle(60.0, _ran(), last=Rate.last)
    assert _arun(nu.ForEachDo(nu.Iter([1, 2, 3]), nm.Frame(Rate, once))) == [1, 1, 1]


def test_throttles_on_different_refs_are_independent() -> None:
    a = nm.Throttle(60.0, _ran(1), last=Rate.last)
    b = nm.Throttle(60.0, _ran(2), last=Rate.other)
    assert _arun(nm.Frame(Rate, a >> b >> a >> b)) == [1, 2]


def test_throttle_refuses_the_sync_runner() -> None:
    with pytest.raises(Exception, match="async"):
        nu.run(nm.Frame(Rate, nm.Throttle(1.0, nu.Add(1, 2), last=Rate.last)))


# --- Debounce --------------------------------------------------------------------


def test_debounce_yields_none_at_once() -> None:
    term = nm.Frame(Rate, nm.Debounce(0.01, nu.Add(1, 2), pending=Rate.pending))
    assert asyncio.run(nu.arun(term))[0] is None


def test_debounce_fires_once_for_a_burst() -> None:
    call = nm.Debounce(0.02, _ran(), pending=Rate.pending)
    burst = nu.ForEachDo(nu.Iter([1, 2, 3]), call) >> nu.Delay(0.1)
    assert _arun(nm.Frame(Rate, burst)) == [1]


def test_debounce_fires_each_call_spaced_past_the_delay() -> None:
    call = nm.Debounce(0.01, _ran(), pending=Rate.pending)
    assert _arun(nm.Frame(Rate, call >> nu.Delay(0.05) >> call >> nu.Delay(0.05))) == [1, 1]


def test_debounce_state_persists_across_a_forever_loop() -> None:
    call = nm.Debounce(0.05, _ran(), pending=Rate.pending)
    loop = nu.Race(nu.ForeverDo(nu.DelayedDo(0.01, call)), nu.Delay(0.2))
    assert _arun(nm.Frame(Rate, loop >> nu.Delay(0.1))) == [1]


def test_debounce_refuses_the_sync_runner() -> None:
    with pytest.raises(Exception, match="async"):
        nu.run(nm.Frame(Rate, nm.Debounce(0.01, nu.Add(1, 2), pending=Rate.pending)))
