"""Redwood DSL - Schema-based tree access layer.

A typed interface for navigating and manipulating persistent tree structures
using schema definitions.

Core concepts:
- Terms: AST nodes representing computations (PathTerm, ValueTerm, CommandTerm)
- Schema: Pure structure definitions using Field types
- Empty/NaN: Special values for missing data and invalid operations
- Metadata: Static analysis information (purity, types, dependencies)
- Operations: View-delegated reads and writes
- Domain Types: Two-class pattern for custom domain logic

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

# Core types
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
from redwood.dsl.values import (
    BinaryOp,
    DomainTypeExpr,
    LiteralValue,
    MethodCallValue,
    PathValue,
    UnaryOp,
)


__all__ = [
    # Core types
    "Empty",
    "NaN",
    "SpecialValue",
    "is_empty",
    "is_nan",
    "is_special",
    "propagate_special",
    # Exceptions
    "DSLError",
    "DSLEvaluationError",
    "DSLPathError",
    "DSLSchemaError",
    "DSLTypeError",
    "DSLViewError",
    # Metadata
    "TermMetadata",
    # Base terms
    "Term",
    "PathTerm",
    "ValueTerm",
    "CommandTerm",
    # Schema system
    "Field",
    "Schema",
    "SchemaField",
    "PrimitiveField",
    # Paths
    "DocumentPath",
    "PrimitivePath",
    # Values
    "PathValue",
    "LiteralValue",
    "BinaryOp",
    "UnaryOp",
    "DomainTypeExpr",
    "MethodCallValue",
    # Operations
    "GetOperation",
    "SetOperation",
    # Commands
    "DeleteCommand",
    "UpdateCommand",
]
