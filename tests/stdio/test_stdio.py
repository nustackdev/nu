"""Tests for the stdio fabric."""

from __future__ import annotations

import asyncio
from io import StringIO
from typing import ClassVar

import pytest

from nu import Context, runtime
from nu.interactions import Debug, Log, Print
from nu.stdio import (
    STDERR,
    STDIN,
    STDOUT,
    BufferedStdio,
    StdioBackend,
    StdioFlush,
    StdioRead,
    StdioRef,
    StdioWrite,
)
from nu.terms.effects import tracked_effects
from nu.terms.types import Effect, Mode


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ctx(
    stdout: StringIO | None = None,
    stderr: StringIO | None = None,
    stdin: StringIO | None = None,
) -> Context:
    """Create Context with StdioBackend using StringIO streams."""
    backend = StdioBackend(
        stdout=stdout or StringIO(),
        stderr=stderr or StringIO(),
        stdin=stdin or StringIO(),
    )
    return Context().bind(StdioBackend, backend)


def _run(coro):
    """Run async in test."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# StdioRef
# ---------------------------------------------------------------------------


class TestStdioRef:
    def test_singletons_exist(self):
        assert STDOUT.name == "stdout"
        assert STDERR.name == "stderr"
        assert STDIN.name == "stdin"

    def test_repr(self):
        assert repr(STDOUT) == "StdioRef.STDOUT"
        assert repr(STDERR) == "StdioRef.STDERR"
        assert repr(STDIN) == "StdioRef.STDIN"

    def test_equality(self):
        assert STDOUT == StdioRef("stdout")
        assert STDOUT != STDERR
        assert STDOUT != "stdout"

    def test_hash(self):
        assert hash(STDOUT) == hash(StdioRef("stdout"))
        s = {STDOUT, STDERR, STDIN}
        assert len(s) == 3

    def test_is_leaf(self):
        assert not STDOUT._children

    def test_resolve(self):
        ctx = _make_ctx()
        assert _run(STDOUT.aresolve(ctx)) == "stdout"

    def test_fetch_with_backend(self):
        out = StringIO()
        ctx = _make_ctx(stdout=out)
        stream = _run(STDOUT.afetch(ctx))
        assert stream is out

    def test_fetch_fallback_to_sys(self):
        import sys

        ctx = Context()  # No StdioBackend bound
        stream = _run(STDOUT.afetch(ctx))
        assert stream is sys.stdout


# ---------------------------------------------------------------------------
# StdioBackend
# ---------------------------------------------------------------------------


class TestStdioBackend:
    def test_stream_for(self):
        out, err, inp = StringIO(), StringIO(), StringIO()
        backend = StdioBackend(stdout=out, stderr=err, stdin=inp)
        assert backend.stream_for(STDOUT) is out
        assert backend.stream_for(STDERR) is err
        assert backend.stream_for(STDIN) is inp

    def test_default_streams(self):
        import sys

        backend = StdioBackend()
        assert backend.stdout is sys.stdout
        assert backend.stderr is sys.stderr
        assert backend.stdin is sys.stdin


# ---------------------------------------------------------------------------
# StdioWrite
# ---------------------------------------------------------------------------


class TestStdioWrite:
    def test_basic_write(self):
        out = StringIO()
        ctx = _make_ctx(stdout=out)
        op = StdioWrite(STDOUT, "hello", "world")
        _run(runtime.aexecute(op, ctx))
        assert out.getvalue() == "hello world\n"

    def test_write_to_stderr(self):
        err = StringIO()
        ctx = _make_ctx(stderr=err)
        op = StdioWrite(STDERR, "error message")
        _run(runtime.aexecute(op, ctx))
        assert err.getvalue() == "error message\n"

    def test_write_overrides(self):
        assert StdioWrite.own_effects == {0: Effect.WRITE}

    def test_effect_tracking(self):
        op = StdioWrite(STDOUT, "hello")
        effects = tracked_effects(op)
        assert (STDOUT, Effect.WRITE) in effects


# ---------------------------------------------------------------------------
# StdioRead
# ---------------------------------------------------------------------------


class TestStdioRead:
    def test_read_line(self):
        inp = StringIO("hello world\n")
        ctx = _make_ctx(stdin=inp)
        op = StdioRead()
        result = _run(runtime.afirst(op, ctx))
        assert result == "hello world"

    def test_no_override(self):
        """StdioRead has no writes (READ is default for bare Ref)."""
        assert getattr(StdioRead, "own_effects", {}) == {}

    def test_effect_tracking(self):
        """StdioRef child produces READ effect via default rule."""
        op = StdioRead()
        effects = tracked_effects(op)
        assert (STDIN, Effect.READ) in effects


# ---------------------------------------------------------------------------
# StdioFlush
# ---------------------------------------------------------------------------


class TestStdioFlush:
    def test_flush(self):
        out = StringIO()
        ctx = _make_ctx(stdout=out)
        op = StdioFlush(STDOUT)
        _run(runtime.aexecute(op, ctx))
        # StringIO.flush() is a no-op but shouldn't error

    def test_overrides(self):
        assert StdioFlush.own_effects == {0: Effect.WRITE}


# ---------------------------------------------------------------------------
# Print / Log / Debug with stdio fabric
# ---------------------------------------------------------------------------


class TestPrintStdio:
    def test_print_writes_to_stdout(self):
        out = StringIO()
        ctx = _make_ctx(stdout=out)
        op = Print("test", 42)
        _run(runtime.aexecute(op, ctx))
        assert "[Print:test] 42" in out.getvalue()

    def test_print_has_write_override(self):
        assert Print.own_effects == {0: Effect.WRITE}

    def test_print_first_child_is_stdio_ref(self):
        op = Print("msg")
        assert isinstance(op._children[0], StdioRef)
        assert op._children[0].name == "stdout"

    def test_print_effect_tracking(self):
        op = Print("test")
        effects = tracked_effects(op)
        assert (STDOUT, Effect.WRITE) in effects


class TestLogStdio:
    def test_log_has_write_override(self):
        assert Log.own_effects == {0: Effect.WRITE}

    def test_log_first_child_is_stderr(self):
        op = Log("msg")
        assert isinstance(op._children[0], StdioRef)
        assert op._children[0].name == "stderr"


class TestDebugStdio:
    def test_debug_writes_to_stdout(self):
        out = StringIO()
        ctx = _make_ctx(stdout=out)
        op = Debug(42, prefix="[DBG]")
        _run(runtime.aexecute(op, ctx))
        assert "[DBG]" in out.getvalue()

    def test_debug_has_write_override(self):
        assert Debug.own_effects == {0: Effect.WRITE}


# ---------------------------------------------------------------------------
# BufferedStdio
# ---------------------------------------------------------------------------


class TestBufferedStdio:
    def test_buffered_writes_flush_on_success(self):
        out = StringIO()
        ctx = _make_ctx(stdout=out)
        op = BufferedStdio(
            StdioWrite(STDOUT, "line 1"),
            StdioWrite(STDOUT, "line 2"),
        )
        _run(runtime.aexecute(op, ctx))
        content = out.getvalue()
        assert "line 1" in content
        assert "line 2" in content

    def test_buffered_writes_discarded_on_failure(self):
        out = StringIO()
        ctx = _make_ctx(stdout=out)

        class FailOp(StdioWrite):
            support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

            def run(self, ctx):
                super().run(ctx)
                raise RuntimeError("boom")

            async def arun(self, ctx):
                await super().arun(ctx)
                raise RuntimeError("boom")

        op = BufferedStdio(
            StdioWrite(STDOUT, "before"),
            FailOp(STDOUT, "after"),
        )
        with pytest.raises(RuntimeError, match="boom"):
            _run(runtime.aexecute(op, ctx))
        # Nothing should have been written to real stdout
        assert out.getvalue() == ""

    def test_buffered_stdin_passes_through(self):
        # stdin reads can't be rolled back, so BufferedStdio passes them through.
        # Verify the buffered backend's stdin is the same object as the real one.
        inp = StringIO("hello\n")
        ctx = _make_ctx(stdin=inp)
        op = BufferedStdio(StdioWrite(STDOUT, "noop"))
        # Drive the bracket: in `before` it captures real_backend; in `after`
        # it flushes. We just verify stdin pass-through directly.
        scoped = op.before(ctx)
        assert scoped.get(StdioBackend).stdin is inp
        op.after(scoped)


# ---------------------------------------------------------------------------
# Effect isolation: stdio vs virtuals
# ---------------------------------------------------------------------------


class TestEffectIsolation:
    def test_stdio_effects_separate_from_calc(self):
        """StdioWrite produces effects, pure ops don't."""
        from nu.interactions import Add

        pure = Add(1, 2)
        assert len(tracked_effects(pure)) == 0

        impure = StdioWrite(STDOUT, "hello")
        assert len(tracked_effects(impure)) == 1

    def test_mixed_tree_effects(self):
        """A composed tree with both stdio and pure ops tracks only stdio effects."""
        from nu.interactions import Add

        # Sequential >> needs Commands; mix two stdio writes around a pure op
        # via a Sequential of two stdio commands. Add is a Query, can't be in
        # body slot, so just compose the two writes.
        tree = StdioWrite(STDOUT, "start") >> StdioWrite(STDERR, "end")
        effects = tracked_effects(tree)
        # Each StdioWrite contributes (Ref, WRITE); two distinct refs
        assert (STDOUT, Effect.WRITE) in effects
        assert (STDERR, Effect.WRITE) in effects
        # Just sanity: pure Add has no effects
        assert len(tracked_effects(Add(1, 2))) == 0
