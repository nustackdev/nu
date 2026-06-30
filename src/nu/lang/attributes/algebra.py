"""Algebra attribute: the rewrite-relevant laws a kind obeys.

Four declared bools per kind: ``commutative`` (children may be reordered),
``associative`` (same-kind nestings may be regrouped), ``idempotent`` (running
the kind twice equals running it once), ``deterministic`` (the same input
yields the same output). No fold and no rule yet - the transformation laws
that read them come later.
"""

from __future__ import annotations

from nu.engine import Attribute, Declared

from .names import Attr


__all__ = ["ATTRIBUTES"]


ATTRIBUTES: tuple[Attribute, ...] = (
    Declared(value=False, name=Attr.COMMUTATIVE),
    Declared(value=False, name=Attr.ASSOCIATIVE),
    Declared(value=False, name=Attr.IDEMPOTENT),
    Declared(value=True, name=Attr.DETERMINISTIC),
)
