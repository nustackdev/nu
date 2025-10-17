"""Redwood DSL - Schema-based tree access layer.

A typed interface for navigating and manipulating persistent tree structures
using schema definitions.

Core concepts:
- Terms: AST nodes representing computations (PathTerm, ValueTerm, CommandTerm)
- Schema: Pure structure definitions using Field types
- Empty/NaN: Special values for missing data and invalid operations
- Metadata: Static analysis information (purity, types, dependencies)
- Operations: View-delegated reads and writes

Example:
    >>> from redwood.dsl import Schema, PrimitiveField, SchemaField
    >>> class Profile(Schema):
    ...     email: str = PrimitiveField(str)
    >>> class User(Schema):
    ...     age: int = PrimitiveField(int)
    ...     profile: Profile = SchemaField(Profile)
    >>> # Query
    >>> is_adult = User.age > 18
    >>> result = is_adult.evaluate(tree, ctx)
    >>> # Mutation
    >>> User.age.set(30).evaluate(tree, ctx)
"""

# Commands
from redwood.dsl.commands import DeleteCommand, UpdateCommand

# Exceptions
from redwood.dsl.exceptions import (
    DSLError,
    DSLEvaluationError,
    DSLPathError,
    DSLSchemaError,
    DSLTypeError,
    DSLViewError,
)

# Metadata
from redwood.dsl.metadata import TermMetadata

# Operations
from redwood.dsl.operations import GetOperation, SetOperation

# Paths
from redwood.dsl.paths import DocumentPath, PrimitivePath

# Schema system
from redwood.dsl.schema import Field, PrimitiveField, Schema, SchemaField

# Base terms
from redwood.dsl.term import CommandTerm, PathTerm, Term, ValueTerm

# Core types
from redwood.dsl.types import (
    Empty,
    NaN,
    SpecialValue,
    is_empty,
    is_nan,
    is_special,
    propagate_special,
)

# Values
from redwood.dsl.values import BinaryOp, LiteralValue, PathValue, UnaryOp


__all__ = [
    "BinaryOp",
    "CommandTerm",
    # Exceptions
    "DSLError",
    "DSLEvaluationError",
    "DSLPathError",
    "DSLSchemaError",
    "DSLTypeError",
    "DSLViewError",
    # Commands
    "DeleteCommand",
    # Paths
    "DocumentPath",
    # Core types
    "Empty",
    # Schema system
    "Field",
    # Operations
    "GetOperation",
    "LiteralValue",
    "NaN",
    "PathTerm",
    # Values
    "PathValue",
    "PrimitiveField",
    "PrimitivePath",
    "Schema",
    "SchemaField",
    "SetOperation",
    "SpecialValue",
    # Base terms
    "Term",
    # Metadata
    "TermMetadata",
    "UnaryOp",
    "UpdateCommand",
    "ValueTerm",
    "is_empty",
    "is_nan",
    "is_special",
    "propagate_special",
]
