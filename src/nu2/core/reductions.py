"""Reduction atoms: fold a stream child down to one value.

Each is a ScalarQuery over a stream. All four are commutative and associative,
so the stream order does not change the result; Max and Min are idempotent too.
"""

from __future__ import annotations

from nu2.engine.structure import Attribute
from nu2.lang import Reduction


__all__ = ["Count", "Max", "Min", "Sum"]


class Sum(Reduction):
    """The sum of every item in its stream child."""

    commutative = Attribute.declared(True)
    associative = Attribute.declared(True)


class Count(Reduction):
    """The number of items in its stream child."""

    commutative = Attribute.declared(True)
    associative = Attribute.declared(True)


class Max(Reduction):
    """The largest item in its stream child."""

    commutative = Attribute.declared(True)
    associative = Attribute.declared(True)
    idempotent = Attribute.declared(True)


class Min(Reduction):
    """The smallest item in its stream child."""

    commutative = Attribute.declared(True)
    associative = Attribute.declared(True)
    idempotent = Attribute.declared(True)
