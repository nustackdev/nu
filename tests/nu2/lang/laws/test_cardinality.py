"""Cardinality laws.

Mirrors ``src/nu2/lang/laws/cardinality.py``. Exercises
``scalar_stream_refused`` and any laws the dimension agent adds
(``reduction_takes_stream``).
"""

from __future__ import annotations

from _support.law_terms import Q, Stream
from _support.laws import assert_fails


def test_scalar_stream_refused_when_query_holds_a_stream() -> None:
    """A scalar consumer (``Q``) fed a stream child - structurally undefined."""
    assert_fails(Q(Stream()), "scalar_stream_refused")
