"""Nu engine: domain-free Symbol + Attribute machinery and the execution driver.

Three subpackages:

- ``engine.structure`` - the alphabet: ``Symbol`` and ``Attribute``.
- ``engine.attribution`` - generic attribute-grammar machinery: ``Program``,
  ``compile``, ``gate``, ``validate``.
- ``engine.execute`` - generic execution driver: ``Runtime``, ``Budget``, and
  the loop primitives.

The engine knows no sorts, no effects, no execution and holds no global state.
A layer-1 language (Nu, in ``nu2.lang``) defines kinds and attributes on top.
"""

from nu2.engine.attribution import (
    Attr,
    Law,
    Path,
    Predicate,
    Program,
    Row,
    Rows,
    Severity,
    Violation,
    compile,
    gate,
    predicate,
    validate,
)
from nu2.engine.execute import Budget, Runtime, into_loop, safely_aclosing, safely_closing
from nu2.engine.structure import Attribute, CycleError, Schema, Symbol, SymbolMeta


__all__ = [
    "Attr",
    "Attribute",
    "Budget",
    "CycleError",
    "Law",
    "Path",
    "Predicate",
    "Program",
    "Row",
    "Rows",
    "Runtime",
    "Schema",
    "Severity",
    "Symbol",
    "SymbolMeta",
    "Violation",
    "compile",
    "gate",
    "into_loop",
    "predicate",
    "safely_aclosing",
    "safely_closing",
    "validate",
]
