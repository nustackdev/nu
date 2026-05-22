"""Nu engine: domain-free Term + Attribute machinery and the execution driver.

Three subpackages:

- ``engine.structure`` - the alphabet: ``Term`` and ``Attribute``.
- ``engine.attribution`` - generic attribute-grammar machinery: ``AttributedTerm``,
  ``attribute``, ``gate``, ``validate``.
- ``engine.evaluation`` - generic execution driver: ``Runtime``, ``Budget``, and
  the loop primitives.

The engine knows no sorts, no effects, no execution and holds no global state.
A layer-1 language (Nu, in ``nu2.lang``) defines kinds and attributes on top.
"""

from nu2.engine.attribution import (
    Attr,
    AttributedTerm,
    Law,
    Path,
    Predicate,
    Row,
    Rows,
    Severity,
    Violation,
    attribute,
    gate,
    predicate,
    validate,
)
from nu2.engine.evaluation import Budget, Runtime, into_loop, safely_aclosing, safely_closing
from nu2.engine.structure import Attribute, CycleError, Schema, Term, TermMeta


__all__ = [
    "Attr",
    "Attribute",
    "AttributedTerm",
    "Budget",
    "CycleError",
    "Law",
    "Path",
    "Predicate",
    "Row",
    "Rows",
    "Runtime",
    "Schema",
    "Severity",
    "Term",
    "TermMeta",
    "Violation",
    "attribute",
    "gate",
    "into_loop",
    "predicate",
    "safely_aclosing",
    "safely_closing",
    "validate",
]
