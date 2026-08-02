"""Tests for the IO core atoms (nu.core.io) - the stdio fabric.

The stdio fabric is wired: ``print`` writes through the stdout Ref, ``input``
reads through the stdin Ref. Tests bind a ``StdioBackend`` on the Context to
capture / script the streams, so nothing touches the real console. We check
both the structure the language assigns (sort, cardinality, the slot-0 fabric
WRITE) and real execution, sync and async.

Logging lives at ``nu.std.logging`` -- see ``tests/nu/std/logging/``.
"""

from __future__ import annotations

import asyncio
import io as _io

from nu import Context, arun, run
from nu.core.io import (
    STDERR,
    STDIN,
    STDOUT,
    Input,
    Print,
    StdioBackend,
    StdioRef,
)
from nu.core.io import input as nu_input
from nu.core.io import print as nu_print
from nu.lang import Cardinality, Sort, compile
from nu.lang.attributes import Attr, Effect


# --- sorts ---------------------------------------------------------------


def test_print_is_a_command() -> None:
    assert Print._sort.value is Sort.SCALAR_COMMAND


def test_input_is_a_scalar_action() -> None:
    assert Input._sort.value is Sort.SCALAR_ACTION


# --- cardinality ---------------------------------------------------------


def test_print_yields_nothing() -> None:
    assert Print._cardinality.value is Cardinality.VOID


def test_input_yields_a_scalar() -> None:
    assert Input._cardinality.value is Cardinality.SCALAR


# --- effect attribution (the slot-0 fabric write) ------------------------


def test_print_declares_a_write_through_its_fabric_ref() -> None:
    program = compile(nu_print("x"))
    effects = program.attr((), Attr.COMPOSITION_EFFECTS)
    # The fabric is identified by the concrete Ref class; print writes to it.
    assert (StdioRef, Effect.WRITE) in effects


def test_input_declares_a_write_through_its_fabric_ref() -> None:
    # Wrapped in a Str; the WRITE propagates up the subtree.
    program = compile(nu_input())
    effects = program.attr((), Attr.COMPOSITION_EFFECTS)
    assert (StdioRef, Effect.WRITE) in effects


def test_input_atom_is_non_deterministic() -> None:
    program = compile(nu_input())
    assert program.attr((0,), "deterministic") is False


# --- functional: execution through a captured backend --------------------


def test_print_writes_to_stdout() -> None:
    buf = _io.StringIO()
    ctx = Context().bind(StdioBackend, StdioBackend(stdout=buf))
    value, _ = run(nu_print("hello", 42), ctx)
    assert value is None  # a Command yields nothing
    assert buf.getvalue() == "hello 42\n"


def test_print_no_args_is_a_blank_line() -> None:
    buf = _io.StringIO()
    ctx = Context().bind(StdioBackend, StdioBackend(stdout=buf))
    run(nu_print(), ctx)
    assert buf.getvalue() == "\n"


def test_input_reads_a_line() -> None:
    inbuf = _io.StringIO("first line\nsecond line\n")
    ctx = Context().bind(StdioBackend, StdioBackend(stdin=inbuf))
    line, _ = run(nu_input(), ctx)
    assert line == "first line"  # newline stripped


def test_print_runs_on_async_path() -> None:
    buf = _io.StringIO()
    ctx = Context().bind(StdioBackend, StdioBackend(stdout=buf))
    asyncio.run(arun(nu_print("async", "world"), ctx))
    assert buf.getvalue() == "async world\n"


def test_input_runs_on_async_path() -> None:
    inbuf = _io.StringIO("typed\n")
    ctx = Context().bind(StdioBackend, StdioBackend(stdin=inbuf))
    line, _ = asyncio.run(arun(nu_input(), ctx))
    assert line == "typed"


# --- Python-identical print kwargs (sep, end, file, flush) ---------------


def test_print_honors_sep_kwarg() -> None:
    buf = _io.StringIO()
    ctx = Context().bind(StdioBackend, StdioBackend(stdout=buf))
    run(nu_print("a", "b", "c", sep=", "), ctx)
    assert buf.getvalue() == "a, b, c\n"


def test_print_honors_end_kwarg() -> None:
    buf = _io.StringIO()
    ctx = Context().bind(StdioBackend, StdioBackend(stdout=buf))
    run(nu_print("no newline", end=""), ctx)
    assert buf.getvalue() == "no newline"


def test_print_empty_sep_and_end() -> None:
    buf = _io.StringIO()
    ctx = Context().bind(StdioBackend, StdioBackend(stdout=buf))
    run(nu_print("a", "b", "c", sep="", end=""), ctx)
    assert buf.getvalue() == "abc"


def test_print_to_stderr_via_file_kwarg() -> None:
    err = _io.StringIO()
    ctx = Context().bind(StdioBackend, StdioBackend(stderr=err))
    run(nu_print("to stderr", file=STDERR), ctx)
    assert err.getvalue() == "to stderr\n"


def test_print_flush_calls_stream_flush() -> None:
    class _Recording(_io.StringIO):
        def __init__(self) -> None:
            super().__init__()
            self.flushed = 0

        def flush(self) -> None:  # type: ignore[override]
            self.flushed += 1

    buf = _Recording()
    ctx = Context().bind(StdioBackend, StdioBackend(stdout=buf))
    run(nu_print("x", flush=True), ctx)
    assert buf.flushed == 1


def test_print_no_flush_by_default() -> None:
    class _Recording(_io.StringIO):
        def __init__(self) -> None:
            super().__init__()
            self.flushed = 0

        def flush(self) -> None:  # type: ignore[override]
            self.flushed += 1

    buf = _Recording()
    ctx = Context().bind(StdioBackend, StdioBackend(stdout=buf))
    run(nu_print("x"), ctx)
    assert buf.flushed == 0


# --- the singletons ------------------------------------------------------


def test_stdout_and_stdin_are_distinct_singletons() -> None:
    assert STDOUT is not STDIN
    assert isinstance(STDOUT, StdioRef)
    assert repr(STDOUT) == "StdioRef.STDOUT"
