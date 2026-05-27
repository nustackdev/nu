"""Span transparency laws.

Mirrors ``src/nu2/lang/laws/spans.py``. Currently the module is empty;
the dimension agent adds ``span_has_body`` and
``span_cardinality_matches_body``. The placeholder test records the
intended green-path shape (a Bracket wrapping a scalar body).
"""

from __future__ import annotations

from _support.law_terms import Brk, Q
from _support.laws import assert_passes


def test_spans_passes_when_bracket_wraps_a_scalar_body() -> None:
    """A Bracket transparently wraps a ScalarQuery body."""
    assert_passes(Brk(Q()))
