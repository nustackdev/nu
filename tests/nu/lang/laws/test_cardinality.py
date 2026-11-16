"""Cardinality laws.

Mirrors ``src/nu/lang/laws/cardinality.py``. Exercises
``scalar_stream_refused`` and ``reduction_takes_stream``: a scalar or void
consumer takes a stream only in its declared reduction slot, and that slot
must hold one.
"""

from __future__ import annotations

import pytest
from _support.law_terms import (
    Act,
    ActRed,
    Brk,
    Cmd,
    CmdRed,
    FlowC,
    FlowS,
    Q,
    R,
    Red,
    Stream,
    StreamAct,
)
from _support.laws import assert_fails, assert_passes, violations

from nu.engine.structure import Declared
from nu.lang import QueryReduction


def test_scalar_stream_refused_passes_when_query_holds_a_scalar() -> None:
    assert_passes(Q(R()))


def test_scalar_stream_refused_fails_when_query_holds_a_stream() -> None:
    assert_fails(Q(Stream()), "scalar_stream_refused")


def test_scalar_stream_refused_fails_when_query_holds_a_stream_action() -> None:
    # A StreamAction yields a stream, so a scalar consumer refuses it exactly
    # like a StreamQuery: the gate is cardinality alone, no per-kind case.
    assert_fails(Q(StreamAct(R())), "scalar_stream_refused")


def test_scalar_stream_refused_passes_when_reduction_holds_a_stream_action() -> None:
    # The consumer names the reduction, so the stream-yielding Action is fine.
    assert_passes(Red(StreamAct(R())))


def test_scalar_stream_refused_passes_when_reduction_holds_a_stream() -> None:
    assert_passes(Red(Stream()))


def test_reduction_takes_stream_passes_when_body_is_stream() -> None:
    assert_passes(Red(Stream()))


def test_reduction_takes_stream_fails_when_body_is_scalar() -> None:
    assert_fails(Red(Q()), "reduction_takes_stream")


def test_reduction_takes_stream_fails_when_body_is_ref() -> None:
    assert_fails(Red(R()), "reduction_takes_stream")


def test_reduction_takes_stream_fails_when_body_missing() -> None:
    assert_fails(Red(), "reduction_takes_stream")


def test_scalar_stream_refused_fails_when_query_holds_stream_through_span() -> None:
    """Span transparency forwards CHILD_CARDINALITY: a Stream wrapped in a
    Bracket still trips the scalar consumer's refusal at the parent."""
    assert_fails(Q(Brk(Stream(R()))), "scalar_stream_refused")


def test_scalar_stream_refused_passes_when_query_holds_scalar_through_span() -> None:
    """Positive control: a scalar body through a Span satisfies the law."""
    assert_passes(Q(Brk(Q(R()))))


# --- reductions across kinds ---------------------------------------------


class RedAt1(QueryReduction):
    """A QueryReduction folding the stream in slot 1, not the default 0."""

    _reduces = Declared(value=1, name="reduces")


# Each base with its stream in the declared slot: Red folds slot 0, the
# write-side bases slot 1 (slot 0 is the Ref they write).
_ACCEPTED = [
    pytest.param(lambda: Red(Stream()), id="query"),
    pytest.param(lambda: ActRed(R(), Stream()), id="action"),
    pytest.param(lambda: CmdRed(R(), Stream()), id="command"),
    pytest.param(lambda: RedAt1(Q(), Stream()), id="query-slot-1"),
]


@pytest.mark.parametrize("build", _ACCEPTED)
def test_each_reduction_base_takes_a_stream_in_its_declared_slot(build) -> None:
    assert_passes(build())


@pytest.mark.parametrize(
    "build",
    [
        pytest.param(lambda: Red(Q()), id="query"),
        pytest.param(lambda: ActRed(R(), Q()), id="action"),
        pytest.param(lambda: CmdRed(R(), Q()), id="command"),
        pytest.param(lambda: RedAt1(Q(), Q()), id="query-slot-1"),
    ],
)
def test_each_reduction_base_refuses_a_scalar_in_its_declared_slot(build) -> None:
    assert_fails(build(), "reduction_takes_stream")


@pytest.mark.parametrize(
    "build",
    [
        pytest.param(lambda: Red(Stream(), Stream()), id="query"),
        pytest.param(lambda: ActRed(Stream(), Stream()), id="action"),
        pytest.param(lambda: CmdRed(Stream(), Stream()), id="command"),
        pytest.param(lambda: RedAt1(Stream(), Stream()), id="query-slot-1"),
    ],
)
def test_a_stream_in_any_other_slot_of_a_reduction_is_refused(build) -> None:
    assert_fails(build(), "scalar_stream_refused")


def test_a_reduction_whose_declared_slot_is_missing_is_refused() -> None:
    assert_fails(ActRed(R()), "reduction_takes_stream")


def test_a_plain_action_with_a_stream_child_is_refused() -> None:
    assert_fails(Act(R(), Stream()), "scalar_stream_refused")


def test_a_plain_command_with_a_stream_child_is_refused() -> None:
    # Commands yield nothing (VOID), yet their slots are scalar like a
    # ScalarQuery's: the refusal covers them too.
    assert_fails(Cmd(R(), Stream()), "scalar_stream_refused")


def test_a_plain_command_with_a_stream_action_child_is_refused() -> None:
    assert_fails(Cmd(R(), StreamAct(R())), "scalar_stream_refused")


def test_a_flow_keeps_taking_streams_where_it_did() -> None:
    # Flows are outside the slot refusal; their own laws govern their slots.
    for flow in (FlowC(Stream(), Cmd(R())), FlowS(Cmd(R()))):
        assert not [v for v in violations(flow) if v.law == "scalar_stream_refused"]


def test_the_refusal_names_the_kind_and_slot() -> None:
    (v,) = [v for v in violations(Cmd(R(), Stream())) if v.law == "scalar_stream_refused"]
    assert "Cmd is fed a stream in slot 1" in v.detail
    assert "it is no reduction" in v.detail


def test_the_refusal_in_a_reduction_names_its_reduction_slot() -> None:
    (v,) = [v for v in violations(ActRed(Stream(), Stream())) if v.law == "scalar_stream_refused"]
    assert "ActRed is fed a stream in slot 0" in v.detail
    assert "only its reduction slot 1 takes a stream" in v.detail


def test_the_reduction_message_names_the_slot_and_what_it_holds() -> None:
    (v,) = [v for v in violations(ActRed(R(), Q())) if v.law == "reduction_takes_stream"]
    assert v.detail == "ActRed folds the stream in slot 1, but it holds a scalar child"
