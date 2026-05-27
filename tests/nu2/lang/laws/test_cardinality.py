"""Cardinality laws.

Mirrors ``src/nu2/lang/laws/cardinality.py``. Exercises
``scalar_stream_refused`` and ``reduction_takes_stream``.
"""

from __future__ import annotations

from _support.law_terms import Q, R, Red, Stream
from _support.laws import assert_fails, assert_passes


def test_scalar_stream_refused_passes_when_query_holds_a_scalar() -> None:
    assert_passes(Q(R()))


def test_scalar_stream_refused_fails_when_query_holds_a_stream() -> None:
    assert_fails(Q(Stream()), "scalar_stream_refused")


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
