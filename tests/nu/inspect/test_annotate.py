"""Tests for nu.inspect.annotate - the logging / step-tracking rewrites.

All annotation logging routes through Python's ``logging`` module (via
``nu.std.logging``). Tests use pytest's ``caplog`` fixture to assert on the
records emitted -- the idiomatic Python way, same as any ``logging`` user.
Print output still routes through the stdio fabric, so tests that also
check ``print`` output still bind a ``StdioBackend``.
"""

from __future__ import annotations

import asyncio
import io as _io
import logging as pylogging
from typing import TYPE_CHECKING

from nu import Context, arun, run
from nu.core import LiteralQuery, PrintCommand
from nu.core.io import STDOUT, StdioBackend
from nu.factory import ScalarQueryFactory
from nu.flows import Sequential
from nu.inspect import annotate_retries, annotate_steps, render_nu
from nu.inspect.annotate import _StepSpan
from nu.lang import Span
from nu.spans.policy import Retry
from nu.std.logging import LogCommand


if TYPE_CHECKING:
    import pytest


def _capture() -> tuple[Context, _io.StringIO]:
    out = _io.StringIO()
    ctx = Context().bind(StdioBackend, StdioBackend(stdout=out))
    return ctx, out


def _prog() -> Sequential:
    return Sequential(
        PrintCommand(STDOUT, LiteralQuery("a")),
        PrintCommand(STDOUT, LiteralQuery("b")),
    )


# --- annotate_steps ----------------------------------------------------------


def test_annotate_steps_wraps_each_child() -> None:
    ann = annotate_steps(_prog())
    assert all(isinstance(c, _StepSpan) for c in ann._children)


def test_step_span_is_a_transparent_span() -> None:
    # the wrapper is a Span (Bracket), so it forwards the body and classifies
    # as a Span in the renderer
    ann = annotate_steps(_prog())
    assert all(isinstance(c, Span) for c in ann._children)


def test_annotate_steps_renders_as_wrapped_box() -> None:
    # the exact box-tree: each step sits under its own _StepSpan brace
    ann = annotate_steps(_prog())
    assert render_nu(ann, as_="plain").splitlines() == [
        "Sequential",
        "├── _StepSpan",
        "│  └── PrintCommand",
        "│     ├── StdioRef(stream='stdout')",
        "│     └── LiteralQuery('a')",
        "└── _StepSpan",
        "   └── PrintCommand",
        "      ├── StdioRef(stream='stdout')",
        "      └── LiteralQuery('b')",
    ]


def test_nested_sequential_logs_a_deeper_path(caplog: pytest.LogCaptureFixture) -> None:
    inner = Sequential(PrintCommand(STDOUT, LiteralQuery("b1")), PrintCommand(STDOUT, LiteralQuery("b2")))
    outer = Sequential(PrintCommand(STDOUT, LiteralQuery("a")), inner)
    caplog.set_level(pylogging.DEBUG, logger="nu.steps")
    run(annotate_steps(outer))
    lines = [r.getMessage() for r in caplog.records]
    # outer steps log under [Sequential]; the inner sequence logs under a deeper
    # path, and its steps nest between the outer step-2 start and done
    out_start = lines.index("[Sequential] step 2/2 start")
    out_done = lines.index("[Sequential] step 2/2 done")
    inner_start = lines.index("[Sequential.Sequential.Sequential] step 1/2 start")
    assert out_start < inner_start < out_done  # inner sequence runs inside outer step 2


def test_annotate_steps_is_idempotent() -> None:
    once = annotate_steps(_prog())
    twice = annotate_steps(once)
    # no double-wrapping: still one _StepSpan per step
    assert all(isinstance(c, _StepSpan) for c in twice._children)
    assert all(not isinstance(c._children[0], _StepSpan) for c in twice._children)


def test_annotate_steps_logs_start_and_done(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(pylogging.DEBUG, logger="nu.steps")
    run(annotate_steps(_prog()))
    records = [(r.levelname, r.name, r.getMessage()) for r in caplog.records]
    assert records == [
        ("INFO", "nu.steps", "[Sequential] step 1/2 start"),
        ("INFO", "nu.steps", "[Sequential] step 1/2 done"),
        ("INFO", "nu.steps", "[Sequential] step 2/2 start"),
        ("INFO", "nu.steps", "[Sequential] step 2/2 done"),
    ]


def test_annotate_steps_logs_failure_and_reraises(caplog: pytest.LogCaptureFixture) -> None:
    def boom() -> object:
        raise RuntimeError("kaboom")

    boom_q = ScalarQueryFactory("BoomQ", boom, deterministic=False)
    prog = Sequential(PrintCommand(STDOUT, LiteralQuery("ok")), PrintCommand(STDOUT, boom_q()))
    caplog.set_level(pylogging.DEBUG, logger="nu.steps")
    try:
        run(annotate_steps(prog))
    except RuntimeError:
        pass
    else:
        raise AssertionError("expected the failure to propagate")
    failure_lines = [(r.levelname, r.getMessage()) for r in caplog.records if "failed" in r.getMessage()]
    assert ("WARNING", "[Sequential] step 2/2 failed: kaboom") in failure_lines


def test_annotate_steps_forwards_result() -> None:
    ctx, out = _capture()
    run(annotate_steps(_prog()), ctx=ctx)
    assert out.getvalue() == "a\nb\n"  # the body still runs, unchanged


# --- annotate_retries --------------------------------------------------------


def _flaky(fail_times: int) -> type:
    state = {"n": 0}

    def body() -> object:
        state["n"] += 1
        if state["n"] <= fail_times:
            raise ValueError(f"fail{state['n']}")
        return "ok"

    return ScalarQueryFactory("Flaky", body, deterministic=False)


def test_annotate_retries_logs_each_failed_attempt(caplog: pytest.LogCaptureFixture) -> None:
    flaky = _flaky(fail_times=2)
    ann = annotate_retries(Retry(flaky(), max_attempts=3, delay=0.0))
    caplog.set_level(pylogging.DEBUG, logger="nu.retry")
    value, _ = asyncio.run(arun(ann))
    assert value == "ok"
    records = [(r.levelname, r.name, r.getMessage()) for r in caplog.records]
    assert records == [
        ("WARNING", "nu.retry", "retry attempt 1 failed: fail1"),
        ("WARNING", "nu.retry", "retry attempt 2 failed: fail2"),
    ]


def test_annotate_retries_injects_a_logcommand_hook() -> None:
    flaky = _flaky(fail_times=1)
    ann = annotate_retries(Retry(flaky(), max_attempts=2, delay=0.0))
    # Retry child slot 5 is on_attempt_fail; it must now hold our LogCommand,
    # while slot 7 (on_fail) stays a Noop so exhaustion still raises
    assert isinstance(ann, Retry)
    assert isinstance(ann._children[5], LogCommand)
    assert type(ann._children[7]).__name__ == "Noop"


def test_annotate_retries_honors_custom_keys(caplog: pytest.LogCaptureFixture) -> None:
    flaky = _flaky(fail_times=1)
    ann = annotate_retries(
        Retry(flaky(), max_attempts=2, delay=0.0, error_key="err", attempt_key="try"),
    )
    caplog.set_level(pylogging.DEBUG, logger="nu.retry")
    asyncio.run(arun(ann))
    # the hook must read the custom keys, so the attempt number and error show up
    assert any("retry attempt 1 failed: fail1" in r.getMessage() for r in caplog.records)


def test_annotate_retries_chains_existing_hook(caplog: pytest.LogCaptureFixture) -> None:
    marker = PrintCommand(STDOUT, LiteralQuery("HOOK"))
    flaky = _flaky(fail_times=1)
    ann = annotate_retries(
        Retry(flaky(), max_attempts=2, delay=0.0, on_attempt_fail=marker),
    )
    out = _io.StringIO()
    ctx = Context().bind(StdioBackend, StdioBackend(stdout=out))
    caplog.set_level(pylogging.DEBUG, logger="nu.retry")
    asyncio.run(arun(ann, ctx=ctx))
    # log runs first, then the original hook -- both fire
    assert any("retry attempt 1 failed: fail1" in r.getMessage() for r in caplog.records)
    assert out.getvalue() == "HOOK\n"


def test_annotate_retries_preserves_the_raise_on_exhaustion() -> None:
    always = _flaky(fail_times=99)
    ann = annotate_retries(Retry(always(), max_attempts=2, delay=0.0))
    # on_fail is NOT hijacked, so exhaustion still raises rather than returning None
    try:
        asyncio.run(arun(ann))
    except ValueError:
        pass
    else:
        raise AssertionError("annotation must not swallow the terminal failure")


