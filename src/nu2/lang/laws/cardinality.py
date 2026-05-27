"""Cardinality laws: scalar / stream / void interplay.

A scalar consumer rejects a stream child (Reduction is the exception, by
design). A Reduction expects its body to resolve to a stream.
"""

from __future__ import annotations

from nu2.engine import Law
from nu2.lang.attributes import Cardinality, Sort

from .predicates import cardinality_is, no_child_yields, of_sort


__all__ = ["LAWS"]


LAWS: tuple[Law, ...] = (
    Law(
        "scalar_stream_refused",
        scope=cardinality_is(Cardinality.SCALAR) & ~of_sort(Sort.REDUCTION),
        holds=no_child_yields(Cardinality.STREAM),
        message="a scalar consumer is fed a stream",
    ),
)
