"""Tests for the Bracket span: Snapshot, Transaction (core lifecycle shells).

A Bracket is a transparent Span (sort BRACKET): it runs the body inside a
``_open`` context manager - open the boundary, yield the scoped ctx the body runs
under, commit on a clean exit or roll back on an exception - forwarding the
body's yield unchanged. At the core level ``_open`` is a pass-through, so a bare
bracket is a pass-through; the suite pins that across void, scalar, and stream
bodies, then drives a recording subclass to pin the lifecycle: _open opens before
the body and closes after, success commits while failure rolls back and
re-propagates, the per-run handle lives in the boundary's frame (not on ``self``),
the body runs under the scoped context which is restored after, and a stream
boundary spans the whole drain (commit fires once, after exhaustion).
"""

from __future__ import annotations

from contextlib import contextmanager

import pytest
from _support.async_atoms import BoomAction

from nu.context import AttrRef, SetCommand
from nu.core import LiteralQuery
from nu.core.iteration import IterQuery
from nu.lang import Attr, Bracket, Cardinality, Span, compile
from nu.lang.helpers import arun, collect, run
from nu.spans import Snapshot, Transaction


def _set(name: str, value: object) -> SetCommand:
    return SetCommand(AttrRef(name), LiteralQuery(value))


# --- basis ----------------------------------------------------------------


def test_snapshot_and_transaction_are_bracket_spans() -> None:
    for cls in (Snapshot, Transaction):
        assert issubclass(cls, Bracket)
        assert issubclass(cls, Span)


def test_bracket_is_transparent_and_forwards_body_cardinality() -> None:
    program = compile(Snapshot(LiteralQuery(5)))
    assert program.attr(program.root, Attr.CARDINALITY) is Cardinality.TRANSPARENT
    assert program.attr(program.root, Attr.CHILD_CARDINALITY) is Cardinality.SCALAR

    stream = compile(Transaction(IterQuery(LiteralQuery([1, 2]))))
    assert stream.attr(stream.root, Attr.CHILD_CARDINALITY) is Cardinality.STREAM


# --- pass-through (core no-op _open) --------------------------------------


def test_snapshot_passes_through_scalar() -> None:
    value, _ = run(Snapshot(LiteralQuery(5)))
    assert value == 5


def test_transaction_passes_through_void() -> None:
    _, ctx = run(Transaction(_set("a", 1)))
    assert ctx.attrs.get("a") == 1


def test_bracket_passes_through_stream() -> None:
    items, _ = collect(compile(Snapshot(IterQuery(LiteralQuery([1, 2, 3])))))
    assert items == [1, 2, 3]


# --- lifecycle ------------------------------------------------------------


def test_transaction_commits_on_success() -> None:
    events: list[str] = []

    class Rec(Transaction):
        @contextmanager
        def _open(self, ctx):
            events.append("open")
            try:
                yield ctx
            except BaseException:
                events.append("rollback")
                raise
            else:
                events.append("commit")

    value, _ = run(Rec(LiteralQuery(7)))
    assert value == 7
    assert events == ["open", "commit"]


def test_transaction_rolls_back_and_reraises_on_failure() -> None:
    events: list[str] = []

    class Rec(Transaction):
        @contextmanager
        def _open(self, ctx):
            events.append("open")
            try:
                yield ctx
            except BaseException:
                events.append("rollback")
                raise
            else:
                events.append("commit")

    with pytest.raises(ValueError, match="boom"):
        run(Rec(BoomAction("boom")))
    assert events == ["open", "rollback"]


def test_per_run_handle_lives_in_the_scope_frame_not_self() -> None:
    opened: list[object] = []
    closed: list[object] = []

    class Rec(Transaction):
        @contextmanager
        def _open(self, ctx):
            handle = object()  # the per-run handle, captured by the frame
            opened.append(handle)
            try:
                yield ctx
            finally:
                closed.append(handle)

    run(Rec(LiteralQuery(1)))
    assert len(opened) == 1
    assert closed == opened


def test_bracket_scopes_ctx_for_body_then_restores() -> None:
    class Scoped(Snapshot):
        @contextmanager
        def _open(self, ctx):
            scoped = ctx._copy()
            scoped.attrs["__scoped__"] = True
            yield scoped

    value, ctx = run(Scoped(AttrRef("__scoped__")))
    assert value is True  # body ran under the scoped ctx
    assert ctx.attrs.get("__scoped__") is None  # restored: the copy was discarded


def test_stream_boundary_spans_the_whole_drain() -> None:
    events: list[str] = []

    class Rec(Transaction):
        @contextmanager
        def _open(self, ctx):
            events.append("open")
            try:
                yield ctx
            except BaseException:
                events.append("rollback")
                raise
            else:
                events.append("commit")

    items, _ = collect(compile(Rec(IterQuery(LiteralQuery([1, 2, 3])))))
    assert items == [1, 2, 3]
    assert events == ["open", "commit"]  # one boundary, committed after exhaustion


# --- async ----------------------------------------------------------------


async def test_transaction_commits_on_success_async() -> None:
    events: list[str] = []

    class Rec(Transaction):
        @contextmanager
        def _open(self, ctx):
            events.append("open")
            try:
                yield ctx
            except BaseException:
                events.append("rollback")
                raise
            else:
                events.append("commit")

    value, _ = await arun(Rec(LiteralQuery(7)))
    assert value == 7
    assert events == ["open", "commit"]


async def test_transaction_rolls_back_on_failure_async() -> None:
    events: list[str] = []

    class Rec(Transaction):
        @contextmanager
        def _open(self, ctx):
            events.append("open")
            try:
                yield ctx
            except BaseException:
                events.append("rollback")
                raise
            else:
                events.append("commit")

    with pytest.raises(ValueError, match="boom"):
        await arun(Rec(BoomAction("boom")))
    assert events == ["open", "rollback"]
