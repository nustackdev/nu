"""Cardinality attribute: how a node yields a result.

A node yields one value, a stream, nothing, or whatever its body yields. The
declared ``cardinality`` fixes that per sort; the synthesized
``child_cardinality`` resolves it, forwarding a Span's body cardinality through
the transparent wrapper so a parent slot-fits the Span by what its body yields.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from nu2.engine.structure import Attribute
from nu2.lang.structure.attrs.names import Attr


if TYPE_CHECKING:
    from nu2.engine.attribution import AttributedTerm
    from nu2.engine.attribution.attributed_term import Path

__all__ = ["ATTRIBUTES", "Cardinality"]


class Cardinality(StrEnum):
    """How a node yields: one value, a stream, nothing, or its body's shape."""

    SCALAR = "scalar"
    STREAM = "stream"
    VOID = "void"
    TRANSPARENT = "transparent"


def _own_cardinality(program: AttributedTerm, path: Path) -> Cardinality:
    """A node's cardinality as its sort declares it, before Span resolution."""
    return program.attr(path, Attr.CARDINALITY)


def _resolve_cardinality(own: Cardinality, kids: list[Cardinality]) -> Cardinality:
    """Resolve cardinality: a Span (declared TRANSPARENT) takes its body's; else fixed."""
    if own is not Cardinality.TRANSPARENT:
        return own
    return kids[0] if kids else Cardinality.VOID


ATTRIBUTES: tuple[Attribute, ...] = (
    Attribute.synthesized(
        Attr.CHILD_CARDINALITY,
        base=_own_cardinality,
        combine=_resolve_cardinality,
        reads=(Attr.CARDINALITY,),
    ),
)
