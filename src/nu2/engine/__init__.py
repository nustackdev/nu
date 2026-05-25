"""Nu engine: domain-free Term + Attribute machinery and a dispatch contract.

Four subpackages, one per phase the engine cares about:

- ``engine.structure``   - the alphabet: ``Term`` and ``Attribute``.
- ``engine.compilation`` - Term -> Program: indexing, attribute sweeps, emit.
- ``engine.validation``  - the validate phase: ``Law``, ``Predicate``, ``gate``, ``validate``.
- ``engine.evaluation``  - the dispatch contract: the ``Runtime`` Protocol.

The engine knows no sorts, no effects, no execution and holds no global state.
A layer-1 language (Nu, in ``nu2.lang``) defines kinds, attributes, and the
concrete Runtime that drives compiled Programs.
"""

from nu2.engine.compilation import Path, Program, compile
from nu2.engine.evaluation import Runtime
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
    "predicate",
    "validate",
]
