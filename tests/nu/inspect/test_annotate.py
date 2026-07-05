"""Tests for nu.inspect.annotate - the logging / step-tracking rewrites.

All annotation logging goes to the stderr side of the stdio fabric, so we bind a
``StdioBackend`` with a ``StringIO`` and assert on what was written. Sync covers
the step spans; async covers the retry hooks (``Retry`` fires hooks only on the
async path).
"""

from __future__ import annotations

import asyncio
import io as _io

from nu import Context, arun, run
from nu.core import LiteralQuery, PrintCommand
from nu.core.io import STDOUT, LogCommand, StdioBackend
from nu.flows import Sequential
from nu.inspect import annotate_retries, annotate_steps, render_nu, set_logger_name
from nu.inspect.annotate import _StepSpan
from nu.lang import Span
from nu.lang.factory import ScalarQueryFactory
from nu.spans.policy import Retry


def _capture() -> tuple[Context, _io.StringIO, _io.StringIO]:
    out, err = _io.StringIO(), _io.StringIO()
    ctx = Context().bind(StdioBackend, StdioBackend(stdout=out, stderr=err))
    return ctx, out, err


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


def test_nested_sequential_logs_a_deeper_path() -> None:
    inner = Sequential(PrintCommand(STDOUT, LiteralQuery("b1")), PrintCommand(STDOUT, LiteralQuery("b2")))
    outer = Sequential(PrintCommand(STDOUT, LiteralQuery("a")), inner)
    ctx, _out, err = _capture()
    run(annotate_steps(outer), ctx=ctx)
    lines = err.getvalue().splitlines()
    # outer steps log under [Sequential]; the inner sequence logs under a deeper
    # path, and its steps nest between the outer step-2 start and done
    out_start = lines.index("[INFO] nu.steps: [Sequential] step 2/2 start")
    out_done = lines.index("[INFO] nu.steps: [Sequential] step 2/2 done")
    inner_start = lines.index("[INFO] nu.steps: [Sequential.Sequential.Sequential] step 1/2 start")
    assert out_start < inner_start < out_done  # inner sequence runs inside outer step 2


def test_annotate_steps_is_idempotent() -> None:
    once = annotate_steps(_prog())
    twice = annotate_steps(once)
    # no double-wrapping: still one _StepSpan per step
    assert all(isinstance(c, _StepSpan) for c in twice._children)
    assert all(not isinstance(c._children[0], _StepSpan) for c in twice._children)


def test_annotate_steps_logs_start_and_done() -> None:
    ctx, _out, err = _capture()
    run(annotate_steps(_prog()), ctx=ctx)
    lines = err.getvalue().splitlines()
    assert lines == [
        "[INFO] nu.steps: [Sequential] step 1/2 start",
        "[INFO] nu.steps: [Sequential] step 1/2 done",
        "[INFO] nu.steps: [Sequential] step 2/2 start",
        "[INFO] nu.steps: [Sequential] step 2/2 done",
    ]


def test_annotate_steps_logs_failure_and_reraises() -> None:
    def boom() -> object:
        raise RuntimeError("kaboom")

    boom_q = ScalarQueryFactory("BoomQ", boom, deterministic=False)
    prog = Sequential(PrintCommand(STDOUT, LiteralQuery("ok")), PrintCommand(STDOUT, boom_q()))
    ctx, _out, err = _capture()
    try:
        run(annotate_steps(prog), ctx=ctx)
    except RuntimeError:
        pass
    else:
        raise AssertionError("expected the failure to propagate")
    assert "[WARNING] nu.steps: [Sequential] step 2/2 failed: kaboom" in err.getvalue()


def test_annotate_steps_forwards_result() -> None:
    ctx, out, _err = _capture()
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


def test_annotate_retries_logs_each_failed_attempt() -> None:
    flaky = _flaky(fail_times=2)
    ann = annotate_retries(Retry(flaky(), max_attempts=3, delay=0.0))
    err = _io.StringIO()
    ctx = Context().bind(StdioBackend, StdioBackend(stderr=err))
    value, _ = asyncio.run(arun(ann, ctx=ctx))
    assert value == "ok"
    lines = err.getvalue().splitlines()
    assert lines == [
        "[WARNING] nu.retry: retry attempt 1 failed: fail1",
        "[WARNING] nu.retry: retry attempt 2 failed: fail2",
    ]


def test_annotate_retries_injects_a_logcommand_hook() -> None:
    flaky = _flaky(fail_times=1)
    ann = annotate_retries(Retry(flaky(), max_attempts=2, delay=0.0))
    # Retry child slot 5 is on_attempt_fail; it must now hold our LogCommand,
    # while slot 7 (on_fail) stays a Noop so exhaustion still raises
    assert isinstance(ann, Retry)
    assert isinstance(ann._children[5], LogCommand)
    assert type(ann._children[7]).__name__ == "Noop"


def test_annotate_retries_honors_custom_keys() -> None:
    flaky = _flaky(fail_times=1)
    ann = annotate_retries(
        Retry(flaky(), max_attempts=2, delay=0.0, error_key="err", attempt_key="try"),
    )
    err = _io.StringIO()
    ctx = Context().bind(StdioBackend, StdioBackend(stderr=err))
    # the hook must read the custom keys, so the attempt number and error show up
    asyncio.run(arun(ann, ctx=ctx))
    assert "retry attempt 1 failed: fail1" in err.getvalue()


def test_annotate_retries_chains_existing_hook() -> None:
    marker = PrintCommand(STDOUT, LiteralQuery("HOOK"))
    flaky = _flaky(fail_times=1)
    ann = annotate_retries(
        Retry(flaky(), max_attempts=2, delay=0.0, on_attempt_fail=marker),
    )
    out, err = _io.StringIO(), _io.StringIO()
    ctx = Context().bind(StdioBackend, StdioBackend(stdout=out, stderr=err))
    asyncio.run(arun(ann, ctx=ctx))
    # log runs first (stderr), then the original hook (stdout) - both fire
    assert "retry attempt 1 failed: fail1" in err.getvalue()
    assert out.getvalue() == "HOOK\n"


def test_annotate_retries_preserves_the_raise_on_exhaustion() -> None:
    always = _flaky(fail_times=99)
    ann = annotate_retries(Retry(always(), max_attempts=2, delay=0.0))
    err = _io.StringIO()
    ctx = Context().bind(StdioBackend, StdioBackend(stderr=err))
    # on_fail is NOT hijacked, so exhaustion still raises rather than returning None
    try:
        asyncio.run(arun(ann, ctx=ctx))
    except ValueError:
        pass
    else:
        raise AssertionError("annotation must not swallow the terminal failure")


# --- set_logger_name ---------------------------------------------------------


def test_set_logger_name_retargets_step_spans() -> None:
    ann = set_logger_name(annotate_steps(_prog()), "custom.log")
    ctx, _out, err = _capture()
    run(ann, ctx=ctx)
    assert "custom.log" in err.getvalue()
    assert "nu.steps" not in err.getvalue()


def test_set_logger_name_retargets_log_commands() -> None:
    flaky = _flaky(fail_times=1)
    ann = set_logger_name(annotate_retries(Retry(flaky(), max_attempts=2, delay=0.0)), "svc")
    err = _io.StringIO()
    ctx = Context().bind(StdioBackend, StdioBackend(stderr=err))
    asyncio.run(arun(ann, ctx=ctx))
    assert "[WARNING] svc: retry attempt 1 failed: fail1" in err.getvalue()
