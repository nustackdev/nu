"""Logic atoms: comparison and boolean ScalarQueries.

Concrete ScalarQuery kinds that yield a boolean. And and Or are commutative,
associative and idempotent; Eq is commutative; Lt and Not are neither.
"""

from __future__ import annotations

from nu2.attribute import Attribute
from nu2.lang import ScalarQuery


__all__ = ["And", "Eq", "Lt", "Not", "Or"]


class Eq(ScalarQuery):
    """Whether its two children are equal."""

    commutative = Attribute.declared(True)


class Lt(ScalarQuery):
    """Whether the first child is less than the second."""


class And(ScalarQuery):
    """The conjunction of its boolean children."""

    commutative = Attribute.declared(True)
    associative = Attribute.declared(True)
    idempotent = Attribute.declared(True)


class Or(ScalarQuery):
    """The disjunction of its boolean children."""

    commutative = Attribute.declared(True)
    associative = Attribute.declared(True)
    idempotent = Attribute.declared(True)


class Not(ScalarQuery):
    """The negation of its one boolean child."""
