"""Span transparency laws.

Mirrors ``src/nu/lang/laws/spans.py``. Exercises ``span_has_body`` and
``span_cardinality_matches_body``.
"""

from __future__ import annotations

from _support.law_terms import Brk, Cmd, Pol, Q, R, Stream
from _support.laws import assert_fails, assert_passes

from nu.engine.structure import Declared
from nu.lang import Bracket, Policy
from nu.lang.attributes import Cardinality


# --- malformed shapes for negative cases -------------------------------


class BrkEmpty(Bracket):
    """A Bracket built with no body for span_has_body coverage."""


class PolEmpty(Policy):
    """A Policy built with no body for span_has_body coverage."""


class BrkScalar(Bracket):
    """A Bracket that wrongly fixes its cardinality to SCALAR.

    Span's whole point is transparency: own cardinality must be
    TRANSPARENT so child_cardinality forwards the body's yield. Pinning it
    to SCALAR breaks the invariant whenever the body is not scalar.
    """

    cardinality = Declared(value=Cardinality.SCALAR)


# --- span_has_body -----------------------------------------------------


def test_span_has_body_passes_when_bracket_wraps_a_body() -> None:
    """A Bracket holding a ScalarQuery has its body slot filled."""
    assert_passes(Brk(Q(R())))


def test_span_has_body_passes_when_policy_wraps_a_body() -> None:
    """A Policy holding a Command has its body slot filled."""
    assert_passes(Pol(Cmd(R())))


def test_span_has_body_fails_when_bracket_has_no_children() -> None:
    """A childless Bracket wraps nothing."""
    assert_fails(BrkEmpty(), "span_has_body")


def test_span_has_body_fails_when_policy_has_no_children() -> None:
    """A childless Policy wraps nothing."""
    assert_fails(PolEmpty(), "span_has_body")


# --- span_cardinality_matches_body -------------------------------------


def test_span_cardinality_matches_body_passes_for_scalar_body() -> None:
    """A canonical Bracket forwards its body's scalar cardinality."""
    assert_passes(Brk(Q(R())))


def test_span_cardinality_matches_body_passes_for_stream_body() -> None:
    """A canonical Bracket forwards its body's stream cardinality."""
    assert_passes(Brk(Stream(R())))


def test_span_cardinality_matches_body_passes_through_nested_span() -> None:
    """Transparency composes: a Bracket wrapping a Policy wrapping a stream."""
    assert_passes(Brk(Pol(Stream(R()))))


def test_span_cardinality_matches_body_fails_when_span_pins_scalar_over_stream() -> None:
    """A Span declaring SCALAR cardinality with a STREAM body lies about its yield."""
    assert_fails(BrkScalar(Stream(R())), "span_cardinality_matches_body")
