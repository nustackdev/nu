"""Engine layer: the validate phase.

Two modules:

- ``predicate`` - the composable ``Predicate`` test plus the ``@predicate``
  decorator. The building block for ``Law.scope`` and ``Law.holds``.
- ``law``       - the ``Law`` rule plus its verdict primitives
  (``Severity``, ``Violation``) and the verdict runners (``gate``,
  ``validate``).

Validation operates over a ``Program`` from ``engine.compilation`` - this
package judges, it never builds.
"""

from nu2.engine.validation.law import (
    Law,
    Message,
    Severity,
    ValidationError,
    Violation,
    gate,
    validate,
)
from nu2.engine.validation.predicate import Predicate, Test, predicate


__all__ = [
    "Law",
    "Message",
    "Predicate",
    "Severity",
    "Test",
    "ValidationError",
    "Violation",
    "gate",
    "predicate",
    "validate",
]
