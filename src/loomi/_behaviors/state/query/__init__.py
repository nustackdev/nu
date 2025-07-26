"""
Query system for declarative tree access.

This package provides a JMESPath-like interface for querying tree data
using natural Python syntax. It supports lazy evaluation, operator overloading,
and complex query composition.

Examples:
    Basic path access:
        query = tree.query()
        email = query.users.alice.email.value()

    Comparisons:
        is_adult = (tree.query().users.alice.age > 18).evaluate(tree)

    Complex queries:
        adults = tree.filter(lambda u: u.age > 18)
        emails = [u.email.value() for u in adults if u.email.exists().evaluate(tree)]
"""

from __future__ import annotations

# Core interfaces and base classes
from .core import LazyOperation, Operand, Operation, Query, ValueQuery

# Concrete implementations
from .evaluator import (
    CachingQueryEvaluator,
    QueryEvaluator,
    get_default_evaluator,
    set_default_evaluator,
)

# Exceptions
from .exceptions import (
    CacheError,
    InvalidOperationError,
    OperandResolutionError,
    OperationNotSupportedError,
    PathNotFoundError,
    QueryError,
    QueryEvaluationError,
    QuerySyntaxError,
)
from .lazy import LazyQuery
from .operands import FunctionOperand, LiteralOperand, PathOperand, QueryOperand
from .operations import (  # Comparison operations; Logical operations; Arithmetic operations; String operations; Unary operations; Registry functions
    OPERATIONS,
    AddOperation,
    AndOperation,
    ContainsOperation,
    DivideOperation,
    EndsWithOperation,
    EqualOperation,
    ExistsOperation,
    GreaterEqualOperation,
    GreaterThanOperation,
    LengthOperation,
    LessEqualOperation,
    LessThanOperation,
    MultiplyOperation,
    NotEqualOperation,
    NotOperation,
    OrOperation,
    StartsWithOperation,
    SubtractOperation,
    get_operation,
    register_operation,
)

# Type definitions
from .types import (
    EvaluatorProtocol,
    OperandProtocol,
    OperationProtocol,
    PathComponent,
    PathList,
    QueryProtocol,
    QueryResult,
)

__all__ = [
    # Core interfaces
    "Query",
    "Operation",
    "Operand",
    "LazyOperation",
    "ValueQuery",
    # Main user interface
    "LazyQuery",
    # Evaluators
    "QueryEvaluator",
    "CachingQueryEvaluator",
    "get_default_evaluator",
    "set_default_evaluator",
    # Operand types
    "PathOperand",
    "LiteralOperand",
    "QueryOperand",
    "FunctionOperand",
    # Comparison operations
    "GreaterThanOperation",
    "LessThanOperation",
    "GreaterEqualOperation",
    "LessEqualOperation",
    "EqualOperation",
    "NotEqualOperation",
    # Logical operations
    "AndOperation",
    "OrOperation",
    "NotOperation",
    # Arithmetic operations
    "AddOperation",
    "SubtractOperation",
    "MultiplyOperation",
    "DivideOperation",
    # String operations
    "ContainsOperation",
    "StartsWithOperation",
    "EndsWithOperation",
    # Unary operations
    "LengthOperation",
    "ExistsOperation",
    # Operation registry
    "OPERATIONS",
    "get_operation",
    "register_operation",
    # Type protocols
    "QueryProtocol",
    "OperationProtocol",
    "OperandProtocol",
    "EvaluatorProtocol",
    "QueryResult",
    "PathComponent",
    "PathList",
    # Exceptions
    "QueryError",
    "QuerySyntaxError",
    "QueryEvaluationError",
    "PathNotFoundError",
    "OperationNotSupportedError",
    "OperandResolutionError",
    "InvalidOperationError",
    "CacheError",
]
