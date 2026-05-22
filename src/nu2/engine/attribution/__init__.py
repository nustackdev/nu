"""Engine layer: generic attribute-grammar machinery.

``attribute`` turns a description plus a schema into an ``AttributedTerm``; ``gate`` and
``validate`` are metaprograms over an attributed program.
"""

from nu2.engine.attribution.attributed_term import Attr, AttributedTerm, Path, Row, Rows, attribute
from nu2.engine.attribution.meta import (
    Law,
    Predicate,
    Severity,
    Violation,
    gate,
    predicate,
    validate,
)


__all__ = [
    "Attr",
    "AttributedTerm",
    "Law",
    "Path",
    "Predicate",
    "Row",
    "Rows",
    "Severity",
    "Violation",
    "attribute",
    "gate",
    "predicate",
    "validate",
]
