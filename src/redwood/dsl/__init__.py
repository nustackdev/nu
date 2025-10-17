"""Redwood DSL - Schema-based tree access layer.

A typed interface for navigating and manipulating persistent tree structures
using schema definitions.

Core concepts:
- Terms: AST nodes representing computations (PathTerm, ValueTerm, CommandTerm)
- Empty/NaN: Special values for missing data and invalid operations
- Metadata: Static analysis information (purity, types, dependencies)

Layer 0 (Foundation):
    - Base term classes
    - Special value system
    - Metadata tracking
    - Exception hierarchy
"""

from redwood.dsl.exceptions import (
    DSLError,
    DSLEvaluationError,
    DSLPathError,
    DSLSchemaError,
    DSLTypeError,
    DSLViewError,
)
from redwood.dsl.metadata import TermMetadata
from redwood.dsl.term import CommandTerm, PathTerm, Term, ValueTerm
from redwood.dsl.types import (
    Empty,
    NaN,
    SpecialValue,
    is_empty,
    is_nan,
    is_special,
    propagate_special,
)


__all__ = [
    # Core types
    "Empty",
    "NaN",
    "SpecialValue",
    # Type checking
    "is_empty",
    "is_nan",
    "is_special",
    "propagate_special",
    # Term hierarchy
    "Term",
    "PathTerm",
    "ValueTerm",
    "CommandTerm",
    # Metadata
    "TermMetadata",
    # Exceptions
    "DSLError",
    "DSLEvaluationError",
    "DSLTypeError",
    "DSLPathError",
    "DSLSchemaError",
    "DSLViewError",
]
