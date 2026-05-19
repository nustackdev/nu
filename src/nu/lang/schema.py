"""Assemble the Nu schema from every concern.

Each concern module exposes an ``ATTRIBUTES`` tuple: its declared defaults and
its computed folds. ``build_schema`` registers them all and finalizes once,
topologically sorting the cross-attribute dependency graph.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.attribute import Schema
from nu.lang import algebra, cardinality, effects, execution, sort


if TYPE_CHECKING:
    from types import ModuleType

__all__ = ["build_schema"]

# The concern modules, each carrying an ``ATTRIBUTES`` tuple.
_CONCERNS: tuple[ModuleType, ...] = (sort, effects, cardinality, execution, algebra)


def build_schema() -> Schema:
    """Build and finalize the Nu schema from every concern's attributes."""
    schema = Schema()
    for concern in _CONCERNS:
        for attribute in concern.ATTRIBUTES:
            schema.register(attribute)
    return schema.finalize()
