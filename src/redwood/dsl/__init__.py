"""Redwood DSL - Declarative query and command system for tree navigation.

A lazy, type-safe expression system for querying and manipulating persistent trees.

Core concepts:
- Terms: AST nodes representing computations (PathTerm, ValueTerm, CommandTerm)
- Empty/NaN: Special values for missing data and invalid operations
- Schema: Pure structure definitions (primitives + containers)
- Views: Access protocols for containers (DictView, ListView, etc.)
- Metadata: Static analysis information (purity, types, dependencies)

Examples:
    >>> # Define schema
    >>> class User(Schema):
    ...     name = Field(primitive=str)
    ...     age = Field(primitive=int)
    ...     orders = Field(view=DictView, schema=Order)
    >>> # Build query (lazy)
    >>> is_adult = User.age > 18
    >>> # Execute query
    >>> with tree.transaction() as ctx:
    ...     result = is_adult.evaluate(tree, ctx)
    >>> # Execute command
    >>> cmd = User.age.set(30)
    >>> with tree.transaction() as ctx:
    ...     cmd.evaluate(tree, ctx)
"""

from __future__ import annotations

from redwood.dsl.commands import DeleteCommand, SetCommand, UpdateCommand
from redwood.dsl.exceptions import (
    DSLError,
    DSLEvaluationError,
    DSLPathError,
    DSLSchemaError,
    DSLTypeError,
    DSLViewError,
)
from redwood.dsl.metadata import TermMetadata
from redwood.dsl.paths import FieldPath, IndexPath, RootPath
from redwood.dsl.schema import Field, Schema
from redwood.dsl.term import CommandTerm, PathTerm, Term, ValueTerm
from redwood.dsl.types import (
    Empty,
    NaN,
    SpecialValue,
    TermResult,
    is_empty,
    is_nan,
    is_special,
    propagate_special,
)
from redwood.dsl.values import BinaryOp, LiteralValue, PathValue, UnaryOp


__all__ = [
    # Core types
    "Empty",
    "NaN",
    "SpecialValue",
    "TermResult",
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
    # Path terms
    "RootPath",
    "FieldPath",
    "IndexPath",
    # Value terms
    "PathValue",
    "LiteralValue",
    "BinaryOp",
    "UnaryOp",
    # Command terms
    "SetCommand",
    "DeleteCommand",
    "UpdateCommand",
    # Schema
    "Schema",
    "Field",
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
