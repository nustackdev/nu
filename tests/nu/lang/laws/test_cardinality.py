"""Cardinality laws.

Mirrors ``src/nu/lang/laws/cardinality.py``. Exercises
``scalar_stream_refused`` and ``reduction_takes_stream``.
"""

from __future__ import annotations

from _support.law_terms import Q, R, Red, Stream, StreamAct
from _support.laws import assert_fails, assert_passes


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
