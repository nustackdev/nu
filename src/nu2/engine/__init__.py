"""Nu engine: domain-free Term + Attribute machinery and the execution driver.

Four subpackages, one per phase the engine cares about:

- ``engine.structure``   - the alphabet: ``Term`` and ``Attribute``.
- ``engine.compilation`` - Term -> Program: indexing, attribute sweeps, emit.
- ``engine.validation``  - the validate phase: ``Law``, ``Predicate``, ``gate``, ``validate``.
- ``engine.evaluation``  - the evaluate phase: ``Runtime``, ``Budget``, loop primitives.

The engine knows no sorts, no effects, no execution and holds no global state.
A layer-1 language (Nu, in ``nu2.lang``) defines kinds and attributes on top.
"""

from nu2.engine.compilation import Path, Program, compile
from nu2.engine.evaluation import Budget, Runtime, into_loop, safely_aclosing, safely_closing
from nu2.engine.structure import (
    Attribute,
    Computed,
    CycleError,
    Declared,
    Inherited,
    NotFinalizedError,
    Schema,
    Synthesized,
    Term,
    TermMeta,
)
from nu2.engine.validation import Law, Predicate, Severity, Violation, gate, predicate, validate


__all__ = [
    "Attribute",
    "Budget",
    "Computed",
    "CycleError",
    "Declared",
    "Inherited",
    "Law",
    "NotFinalizedError",
    "Path",
    "Predicate",
    "Program",
    "Runtime",
    "Schema",
    "Severity",
    "Synthesized",
    "Term",
    "TermMeta",
    "Violation",
    "compile",
    "gate",
    "into_loop",
    "predicate",
    "safely_aclosing",
    "safely_closing",
    "validate",
]
