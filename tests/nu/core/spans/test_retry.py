"""Tests for the Retry policy span - full v1 parity.

Sync is a basic retry (max_attempts + errors); async adds unbounded attempts,
delay/backoff/max_delay/jitter and the on_attempt_fail / on_success / on_fail hooks (each against an isolated
ctx copy carrying attempt + error). A stream body is retried by atomic
re-evaluation.
"""

from __future__ import annotations

import asyncio

import pytest
from _support.policy_atoms import FlakyAction, FlakyStream, RecordAction

import nu
from nu.core import Add
from nu.core.flows import Noop
from nu.core.spans import Retry, policy
from nu.lang import Attr, Cardinality, Literal, Policy, Span
from nu.lang.helpers import acollect, arun, collect, compile, run


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
    flaky = FlakyAction(1)
    value, _ = run(Retry(flaky, max_attempts=3))
    assert value == "flaky"
    assert next(flaky.calls) == 2  # failed once, then succeeded


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
    await arun(
        Retry(
            FlakyAction(0),
            max_attempts=3,
            on_success=lambda attempt: RecordAction(log, "ok", attempt=attempt),
        )
    )
    assert log == [("ok", 1, None)]


async def test_async_attempt_fail_and_fail_hooks_fire() -> None:
    log: list = []
    value, _ = await arun(
        Retry(
            FlakyAction(5),
            max_attempts=2,
            on_attempt_fail=lambda err: RecordAction(log, "af", error=err),
            on_fail=lambda err, attempt: RecordAction(log, "fail", attempt=attempt, error=err),
        ),
    )
    assert value is None  # on_fail present -> swallow, return None
    tags = [entry[0] for entry in log]
    assert tags == ["af", "fail"]
    assert log[-1][1:] == (2, "flaky 1")  # the fail hook got the attempt and the error


async def test_async_a_noop_on_fail_still_swallows() -> None:
    value, _ = await arun(Retry(FlakyAction(5), max_attempts=2, on_fail=Noop()))
    assert value is None


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


# --- unbounded attempts ---------------------------------------------------


async def test_async_unbounded_retries_until_success() -> None:
    flaky = FlakyAction(25)
    value, _ = await arun(Retry(flaky, max_attempts=None))
    assert value == "flaky"
    assert next(flaky.calls) == 26  # 25 failures, then the success


async def test_async_unbounded_runs_until_cancelled() -> None:
    flaky = FlakyAction(10**9)
    task = asyncio.ensure_future(arun(Retry(flaky, max_attempts=None, on_fail=Noop())))
    await asyncio.sleep(0.02)
    assert not task.done()  # never exhausts, so on_fail never runs
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert next(flaky.calls) > 3


async def test_async_unbounded_still_lets_an_unmatched_error_through() -> None:
    with pytest.raises(ValueError, match="flaky"):
        await arun(Retry(FlakyAction(5), max_attempts=None, errors=KeyError))


async def test_async_unbounded_stream_retries_until_success() -> None:
    items, _ = await acollect(compile(Retry(FlakyStream(7, [1, 2]), max_attempts=None)))
    assert items == [1, 2]


def test_sync_unbounded_raises() -> None:
    """Sync has no delay, so an unbounded retry would spin: it is refused when run."""
    with pytest.raises(ValueError, match="max_attempts=None needs the async runtime"):
        run(Retry(FlakyAction(0), max_attempts=None))


# --- the waits: backoff, max_delay, jitter --------------------------------


@pytest.fixture
def waits(monkeypatch: pytest.MonkeyPatch) -> list:
    """The waits Retry sleeps, recorded instead of slept."""
    slept: list = []

    async def sleep(seconds: float) -> None:
        slept.append(seconds)

    monkeypatch.setattr(policy.asyncio, "sleep", sleep)
    return slept


async def test_async_backoff_grows_the_wait(waits: list) -> None:
    await arun(Retry(FlakyAction(3), max_attempts=4, delay=1.0, backoff=2.0))
    assert waits == [1.0, 2.0, 4.0]


async def test_async_max_delay_caps_the_grown_wait(waits: list) -> None:
    await arun(Retry(FlakyAction(4), max_attempts=5, delay=1.0, backoff=3.0, max_delay=5.0))
    assert waits == [1.0, 3.0, 5.0, 5.0]


async def test_async_max_delay_caps_the_first_wait_too(waits: list) -> None:
    await arun(Retry(FlakyAction(1), max_attempts=2, delay=10.0, max_delay=2.0))
    assert waits == [2.0]


async def test_async_jitter_applies_after_the_cap(
    waits: list, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(policy.random, "uniform", lambda lo, hi: hi)  # the widest spread up
    await arun(
        Retry(FlakyAction(3), max_attempts=4, delay=1.0, backoff=10.0, jitter=0.5, max_delay=4.0)
    )
    assert waits == [1.5, 6.0, 6.0]  # 1, then capped 4 and 4, each spread by +50%


async def test_async_max_delay_is_a_child_term(waits: list) -> None:
    cap = Add(Literal(1), Literal(2))
    retry = Retry(FlakyAction(2), max_attempts=3, delay=8.0, max_delay=cap)
    assert nu.tree.children(retry)[8] is cap  # a child, before the errors filter
    await arun(retry)
    assert waits == [3.0, 3.0]


def test_negative_plain_max_delay_raises_at_build() -> None:
    with pytest.raises(ValueError, match="Retry: max_delay must not be negative"):
        Retry(FlakyAction(1), max_attempts=2, max_delay=-1.0)


async def test_async_negative_literal_max_delay_raises_when_run() -> None:
    # A term is a child like any other: Retry does not look inside it at build.
    retry = Retry(FlakyAction(1), max_attempts=2, max_delay=Literal(-1.0))
    with pytest.raises(ValueError, match="Retry: max_delay must not be negative"):
        await arun(retry)


async def test_async_negative_computed_max_delay_raises_when_run() -> None:
    retry = Retry(FlakyAction(1), max_attempts=2, max_delay=Add(Literal(-2.0), Literal(1.0)))
    with pytest.raises(ValueError, match="Retry: max_delay must not be negative"):
        await arun(retry)


async def test_async_stream_waits_between_attempts(waits: list) -> None:
    items, _ = await acollect(
        compile(Retry(FlakyStream(2, [1]), max_attempts=3, delay=1.0, backoff=2.0))
    )
    assert items == [1]
    assert waits == [1.0, 2.0]


# --- except_errors: what is never retried ---------------------------------


class Gate(nu.Shape):
    """The flag a computed exclusion reads."""

    flag = nu.BoolRef.slot()


def test_sync_excluded_error_raises_on_the_first_attempt() -> None:
    flaky = FlakyAction(5)
    with pytest.raises(ValueError, match="flaky 0"):
        run(Retry(flaky, max_attempts=3, except_errors=ValueError))
    assert next(flaky.calls) == 1  # one attempt only


def test_sync_an_error_outside_the_exclusion_still_retries() -> None:
    flaky = FlakyAction(2)
    value, _ = run(Retry(flaky, max_attempts=3, except_errors=KeyError))
    assert value == "flaky"
    assert next(flaky.calls) == 3


def test_sync_exclusion_wins_over_a_matching_errors_filter() -> None:
    flaky = FlakyAction(5)
    with pytest.raises(ValueError, match="flaky 0"):
        run(Retry(flaky, max_attempts=3, errors=ValueError, except_errors=ValueError))
    assert next(flaky.calls) == 1


def test_sync_stream_excluded_error_raises_on_the_first_attempt() -> None:
    with pytest.raises(ValueError, match="fs 0"):
        collect(compile(Retry(FlakyStream(1, [1]), max_attempts=3, except_errors=ValueError)))


async def test_async_excluded_error_raises_unretried_and_without_hooks() -> None:
    flaky, log = FlakyAction(5), []
    retry = Retry(
        flaky,
        max_attempts=3,
        except_errors=ValueError,
        on_attempt_fail=RecordAction(log, "af"),
        on_fail=RecordAction(log, "fail"),
    )
    with pytest.raises(ValueError, match="flaky 0"):
        await arun(retry)
    assert next(flaky.calls) == 1
    assert log == []  # on_fail does not swallow an excluded error


async def test_async_an_error_outside_the_exclusion_still_retries() -> None:
    value, _ = await arun(Retry(FlakyAction(2), max_attempts=3, except_errors=KeyError))
    assert value == "flaky"


async def test_async_exclusion_wins_over_a_matching_errors_filter() -> None:
    flaky = FlakyAction(5)
    with pytest.raises(ValueError, match="flaky 0"):
        await arun(Retry(flaky, max_attempts=None, errors=ValueError, except_errors=ValueError))
    assert next(flaky.calls) == 1


async def test_async_stream_excluded_error_raises_on_the_first_attempt() -> None:
    retry = Retry(FlakyStream(1, [1]), max_attempts=3, except_errors=(KeyError, ValueError))
    with pytest.raises(ValueError, match="fs 0"):
        await acollect(compile(retry))


def test_exclusion_is_computed() -> None:
    excluded = nu.If(Gate.flag, ValueError, KeyError)
    retry = Retry(FlakyAction(1), max_attempts=2, except_errors=excluded)
    assert nu.tree.children(retry)[10] is excluded  # appended after the errors filter
    with pytest.raises(ValueError, match="flaky 0"):
        run(nu.let(Gate, retry, flag=True))
    value, _ = run(
        nu.let(Gate, Retry(FlakyAction(1), max_attempts=2, except_errors=excluded), flag=False)
    )
    assert value == "flaky"


async def test_exclusion_is_computed_on_the_async_path() -> None:
    excluded = nu.If(Gate.flag, ValueError, KeyError)
    with pytest.raises(ValueError, match="flaky 0"):
        await arun(
            nu.let(Gate, Retry(FlakyAction(1), max_attempts=2, except_errors=excluded), flag=True)
        )


def test_a_non_exception_exclusion_is_refused_at_build() -> None:
    with pytest.raises(TypeError, match="must be exception classes"):
        Retry(FlakyAction(1), except_errors=int)  # type: ignore[arg-type]


async def test_async_hooks_read_the_exception_as_a_catch_does() -> None:
    seen: list = []
    hook = nu.host(seen.append, name="Seen")
    retry = Retry(
        FlakyAction(5),
        max_attempts=2,
        on_attempt_fail=lambda err, attempt: hook(nu.GetAttr(err, "exception")),
        on_fail=lambda err, attempt: hook(err),
    )
    await arun(retry)
    assert isinstance(seen[0], ValueError)
    assert seen[1] == "flaky 1"
    assert isinstance(seen[1].exception, ValueError)
