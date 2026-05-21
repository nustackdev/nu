"""Engine layer: generic attribute-grammar machinery.

``compile`` turns a description plus a schema into a ``Program``; ``gate`` and
``validate`` are metaprograms over a compiled program.
"""

from nu2.engine.attribution.meta import (
    Law,
    Predicate,
    Severity,
    Violation,
    gate,
    predicate,
    validate,
)
from nu2.engine.attribution.program import Attr, Path, Program, Row, Rows, compile


__all__ = [
    "Attr",
    "Law",
    "Path",
    "Predicate",
    "Program",
    "Row",
    "Rows",
    "Severity",
    "Violation",
    "compile",
    "gate",
    "predicate",
    "validate",
]
