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

from .builder import QueryBuilder
from .evaluator import QueryEvaluator, get_default_evaluator, set_default_evaluator
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
from .operands import FunctionOperand, LiteralOperand, Operand, PathOperand, QueryOperand
from .operations import (
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
    Operation,
    OrOperation,
    StartsWithOperation,
    SubtractOperation,
    get_operation,
    register_operation,
)
from .queries import OperationQuery, PathQuery, Query
from .types import (
    EvaluatorProtocol,
    OperandProtocol,
    OperationProtocol,
    Path,
    PathComponent,
    QueryProtocol,
    QueryResult,
)

__all__ = [
    # Core interfaces
    "Query",
    "Operation",
    "Operand",
    # Query implementations
    "PathQuery",
    "OperationQuery",
    # Main user interface
    "QueryBuilder",
    # Evaluators
    "QueryEvaluator",
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
    "Path",
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
