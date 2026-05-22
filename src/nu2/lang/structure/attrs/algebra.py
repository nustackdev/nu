"""Algebra attribute: the rewrite-relevant laws a kind obeys.

Four declared bools per kind: ``commutative`` (children may be reordered),
``associative`` (same-kind nestings may be regrouped), ``idempotent`` (running
the kind twice equals running it once), ``deterministic`` (the same input
yields the same output). No fold and no rule yet - the transformation laws
that read them come later.
"""

from __future__ import annotations

from nu2.engine.structure import Attribute
from nu2.lang.structure.attrs.names import Attr


__all__ = ["ATTRIBUTES"]


ATTRIBUTES: tuple[Attribute, ...] = (
    Attribute.declared(value=False, name=Attr.COMMUTATIVE),
    Attribute.declared(value=False, name=Attr.ASSOCIATIVE),
    Attribute.declared(value=False, name=Attr.IDEMPOTENT),
    Attribute.declared(value=True, name=Attr.DETERMINISTIC),
)
