"""Tests for the Bracket span: Snapshot, Transaction (core lifecycle shells).

A Bracket is a transparent Span (sort BRACKET): it runs the body inside a
``_open`` context manager - open the boundary, yield the Context the body runs
on with what it provides, commit on a clean exit or roll back on an exception - forwarding the
body's yield unchanged. At the core level ``_open`` is a pass-through, so a bare
bracket is a pass-through; the suite pins that across void, scalar, and stream
bodies, then drives a recording subclass to pin the lifecycle: _open opens before
the body and closes after, success commits while failure rolls back and
re-propagates, the per-run handle lives in the boundary's frame (not on ``self``),
the body sees what the boundary provides and its caller never does, and a stream
boundary spans the whole drain (commit fires once, after exhaustion).
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

import pytest
from _support.async_atoms import BoomAction
from _support.law_terms import Cmd, Q, R
from _support.laws import assert_fails, assert_passes

import nu
from nu.context import FabricRef
from nu.core.arithmetic import Add
from nu.core.iteration import Iter
from nu.core.spans import Snapshot, Transaction
from nu.lang import Attr, Bracket, Cardinality, Literal, Span
from nu.lang.helpers import arun, collect, compile, run


if TYPE_CHECKING:
    from nu.domains.shape.interactions import SetCmd


class S(nu.Shape):
    """The mem slot the pass-through body writes."""

    a = nu.mem.ObjectRef.slot()


def _set(name: str, value: object) -> SetCmd:
    return getattr(S, name).set(Literal(value))


# --- basis ----------------------------------------------------------------


def test_snapshot_and_transaction_are_bracket_spans() -> None:
    for cls in (Snapshot, Transaction):
        assert issubclass(cls, Bracket)
        assert issubclass(cls, Span)


# --- the Gor scenario -----------------------------------------------------
#
# A scalar-value consumer must reject a Command wrapped in any Span shape,
# and accept a yielder wrapped in the same shape. Sort transparency is not
# a bypass: the parent still sees the body's sort through the wrapper.


@pytest.mark.parametrize("span_cls", [Bracket, Snapshot, Transaction])
def test_gor_scenario_add_rejects_command_through_span(span_cls: type) -> None:
    """``Add(Span(Cmd(R())), 3)`` fires ``composition`` for every Span shape."""
    assert_fails(Add(span_cls(Cmd(R())), Literal(3)), "composition")


@pytest.mark.parametrize("span_cls", [Bracket, Snapshot, Transaction])
def test_gor_scenario_add_accepts_yielder_through_span(span_cls: type) -> None:
    """Positive control: a yielder wrapped in the same Span shape passes."""
    assert_passes(Add(span_cls(Q(R())), Literal(3)))


# --- other Span basics ----------------------------------------------------


def test_bracket_is_transparent_and_forwards_body_cardinality() -> None:
    program = compile(Snapshot(Literal(5)))
    assert program.attr(program.root, Attr.CARDINALITY) is Cardinality.TRANSPARENT
    assert program.attr(program.root, Attr.CHILD_CARDINALITY) is Cardinality.SCALAR

    stream = compile(Transaction(Iter(Literal([1, 2]))))
    assert stream.attr(stream.root, Attr.CHILD_CARDINALITY) is Cardinality.STREAM


# --- pass-through (core no-op _open) --------------------------------------


def test_snapshot_passes_through_scalar() -> None:
    value, _ = run(Snapshot(Literal(5)))
    assert value == 5


def test_transaction_passes_through_void() -> None:
    data: dict = {}
    run(Transaction(_set("a", 1)), nu.Context().bind(dict, data, S))
    assert data == {"a": 1}


def test_bracket_passes_through_stream() -> None:
    items, _ = collect(compile(Snapshot(Iter(Literal([1, 2, 3])))))
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

    value, _ = run(Rec(Literal(7)))
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

    run(Rec(Literal(1)))
    assert len(opened) == 1
    assert closed == opened


def test_bracket_pushes_a_frame_for_the_body_only() -> None:
    class Marker:
        pass

    class Scoped(Snapshot):
        @contextmanager
        def _open(self, ctx):
            yield ctx.bind(Marker, Marker())

    value, ctx = run(Scoped(FabricRef(Marker).exists()))
    assert value is True  # body ran with the binding provided
    assert not ctx.has(Marker)  # the frame was the body's alone


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

    items, _ = collect(compile(Rec(Iter(Literal([1, 2, 3])))))
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

    value, _ = await arun(Rec(Literal(7)))
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


# --- config children --------------------------------------------------------


def _configured(seen: list) -> type[Transaction]:
    """A bracket with two config children after the body: ``[body, label, scale]``."""

    class Configured(Transaction):
        def __init__(self, body: object, label: object, scale: object) -> None:
            super().__init__(body, label, scale)

        @contextmanager
        def _open(self, ctx, label, scale):
            seen.append(("open", label, scale))
            yield ctx
            seen.append(("close", label))

    return Configured


def test_config_children_reach_open_evaluated_in_order() -> None:
    seen: list = []
    value, _ = run(_configured(seen)(Literal(7), "a", Add(2, 3)))
    assert value == 7
    assert seen == [("open", "a", 5), ("close", "a")]


async def test_config_children_reach_aopen_through_the_default() -> None:
    seen: list = []
    value, _ = await arun(_configured(seen)(Literal(7), "a", Add(2, 3)))
    assert value == 7
    assert seen == [("open", "a", 5), ("close", "a")]


def test_config_children_open_a_stream_body_around_the_whole_drain() -> None:
    seen: list = []
    items, _ = collect(compile(_configured(seen)(Iter(Literal([1, 2])), "s", 1)))
    assert items == [1, 2]
    assert seen == [("open", "s", 1), ("close", "s")]


def test_config_children_leave_the_body_in_the_transparent_slot() -> None:
    program = compile(_configured([])(Iter(Literal([1, 2])), "s", 1))
    assert program.attr(program.root, Attr.CHILD_CARDINALITY) is Cardinality.STREAM


def test_enter_opens_a_bracket_with_its_config_outside_a_tree() -> None:
    seen: list = []
    with _configured(seen)(Literal(None), "x", Add(1, 1))._enter(nu.Context()):
        assert seen == [("open", "x", 2)]
    assert seen[-1] == ("close", "x")
