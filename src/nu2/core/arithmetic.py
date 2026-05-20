"""Arithmetic atoms: literals and the numeric ScalarQueries.

Concrete ScalarQuery kinds on ``nu2.lang``. A Literal carries a constant in its
payload; Add and Mul are commutative and associative, Sub, Div and Neg are
neither. None touch the Context on their own - effects come from Ref children.
"""

from __future__ import annotations

from nu2.attribute import Attribute
from nu2.lang import ScalarQuery


__all__ = ["Add", "Div", "Literal", "Mul", "Neg", "Sub"]


class Literal(ScalarQuery):
    """A ScalarQuery that yields a constant value carried in its payload."""

    def __init__(self, value: object) -> None:
        super().__init__()
        self.payload = {"value": value}


class Add(ScalarQuery):
    """The sum of its scalar children."""

    commutative = Attribute.declared(True)
    associative = Attribute.declared(True)


class Mul(ScalarQuery):
    """The product of its scalar children."""

    commutative = Attribute.declared(True)
    associative = Attribute.declared(True)


class Sub(ScalarQuery):
    """The first child minus the second."""


class Div(ScalarQuery):
    """The first child divided by the second."""


class Neg(ScalarQuery):
    """The arithmetic negation of its one child."""
