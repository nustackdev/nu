"""Nu engine: domain-free Term + Attribute machinery and the execution driver.

Four subpackages, one per phase the engine cares about:

- ``engine.structure``   - the alphabet: ``Term`` and ``Attribute``.
- ``engine.attribution`` - the attribute phase: ``AttributedTerm``, ``attribute``.
- ``engine.validation``  - the validate phase: ``Law``, ``Predicate``, ``gate``, ``validate``.
- ``engine.evaluation``  - the evaluate phase: ``Runtime``, ``Budget``, loop primitives.

The engine knows no sorts, no effects, no execution and holds no global state.
A layer-1 language (Nu, in ``nu2.lang``) defines kinds and attributes on top.
"""

from nu2.engine.attribution import Attr, AttributedTerm, Path, Row, Rows, attribute
from nu2.engine.evaluation import Budget, Runtime, into_loop, safely_aclosing, safely_closing
from nu2.engine.structure import Attribute, CycleError, Schema, Term, TermMeta
from nu2.engine.validation import Law, Predicate, Severity, Violation, gate, predicate, validate


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
