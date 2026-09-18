"""Engine layer: structure.

The engine's alphabet -- the primitives every layer-1 language reuses.

- :class:`Term`, :class:`TermMeta` -- the node and its metaclass.
- :class:`Attribute` and its three concrete kinds -- :class:`Declared`,
  :class:`Synthesized`, :class:`Inherited` -- the named values attached to
  Term classes. :class:`Computed` is the abstract base shared by the two
  computed kinds.
- :class:`Schema` -- the tree-wide attribute registry plus the finalized
  cross-attribute dependency order.
- :exc:`CycleError`, :exc:`NotFinalizedError` -- structural failures.
- :data:`RuleFn` -- the type alias for attribute rule callables.
"""

from .attribute import (
    Attribute,
    Computed,
    Declared,
    Inherited,
    Synthesized,
)
from .exceptions import CycleError, NotFinalizedError
from .schema import Schema
from .term import Term, TermMeta
from .types import RuleFn


__all__ = [
    "Attribute",
    "Computed",
    "CycleError",
    "Declared",
    "Inherited",
    "NotFinalizedError",
    "RuleFn",
    "Schema",
    "Synthesized",
    "Term",
    "TermMeta",
]
