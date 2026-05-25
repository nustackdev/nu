"""Nu's attributes: one module per concern, plus the schema that assembles them.

Each concern module here owns its value space (an enum) and its ``ATTRIBUTES``
tuple: declared defaults plus computed folds. ``build_schema`` registers every
concern's attributes and finalizes once, topologically sorting the
cross-attribute dependency graph.

This package is the home of the *names* (``Attr``), the *value enums* and the
*attribute definitions*. The user-facing Term classes that declare these on
their bindings live one level up in ``nu2.lang.kinds``.
"""

from __future__ import annotations

from nu2.engine import Schema

from . import algebra, cardinality, effects, execution, sort
from .cardinality import Cardinality
from .effects import Effect, EffectSet
from .execution import ExecOrder
from .names import Attr
from .sort import MATRIX, Sort, matrix_sort, subsort


__all__ = [
    "MATRIX",
    "Attr",
    "Cardinality",
    "Effect",
    "EffectSet",
    "ExecOrder",
    "Sort",
    "build_schema",
    "matrix_sort",
    "subsort",
]


_CONCERNS = (sort, effects, cardinality, execution, algebra)


def build_schema() -> Schema:
    """Build and finalize the Nu schema from every concern's attributes."""
    schema = Schema()
    for concern in _CONCERNS:
        for attribute in concern.ATTRIBUTES:
            schema.register(attribute)
    return schema.finalize()
