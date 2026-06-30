"""Cardinality laws: scalar / stream / void interplay.

A scalar consumer rejects a stream child (Reduction is the exception, by
design). A Reduction expects its body to resolve to a stream.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine import Law, predicate
from nu.lang.attributes import Attr, Cardinality, Sort

from .predicates import cardinality_is, child_paths, no_child_yields, of_sort


if TYPE_CHECKING:
    from nu.engine import Path, Program


__all__ = ["LAWS"]


@predicate
def body_yields_stream(program: Program, path: Path) -> bool:
    """Holds when the node's body-slot child has STREAM child_cardinality."""
    children = child_paths(program, path)
    if not children:
        return False
    return program.attr(children[0], Attr.CHILD_CARDINALITY) is Cardinality.STREAM


LAWS: tuple[Law, ...] = (
    Law(
        "scalar_stream_refused",
        scope=cardinality_is(Cardinality.SCALAR) & ~of_sort(Sort.REDUCTION),
        holds=no_child_yields(Cardinality.STREAM),
        message="a scalar consumer is fed a stream",
    ),
    Law(
        "reduction_takes_stream",
        scope=of_sort(Sort.REDUCTION),
        holds=body_yields_stream,
        message="a Reduction expects a stream body",
    ),
)
