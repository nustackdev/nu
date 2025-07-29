"""
Query module for chainable operations on paths.

This module provides an immutable query system that enables fluent, chainable
operations on path objects through operator overloading. Queries build operation
trees that can be evaluated lazily against tree data.

Core Components:
- Query: Main class for chainable operations with operator overloading
- Operations: Immutable operation hierarchy with calc() methods
- QueryEvaluator: Coordinates evaluation of operation trees against tree data
- Query types and protocols: Type safety and clear interfaces

Architecture:
- Query objects are immutable and always return new Query objects
- Operations contain their operands and handle their own computation
- Everything is an operation (including path resolution) for consistency
- Evaluation is separate from construction for lazy execution

Example Usage:
    ```python
    # Create query from path
    query = tree.P.users.alice.age.Q()

    # Chain operations using operators
    result = (query + 10 + 5 > 18 and
             tree.P.users.alice.status.Q() == "active")

    # Evaluate against tree
    is_valid = result.evaluate(tree)

    # Complex expressions
    adults = tree.P.users.Q().filter(lambda u: u.age.Q() > 18)
    ```
"""

from .evaluator import QueryEvaluator
from .exceptions import QueryError, QueryEvaluationError, QueryOperationError, QuerySyntaxError
from .operations import (  # Base classes; Path resolution; Arithmetic operations; Comparison operations; Logical operations; String operations; Function operations
    AbsOperation,
    AddOperation,
    AndOperation,
    AnyOperation,
    BinaryOperation,
    BoolOperation,
    ContainsOperation,
    CountOperation,
    DivideOperation,
    EndsWithOperation,
    EqualOperation,
    EveryOperation,
    GreaterEqualOperation,
    GreaterThanOperation,
    LengthOperation,
    LessEqualOperation,
    LessThanOperation,
    MaxOperation,
    MinOperation,
    ModuloOperation,
    MultiplyOperation,
    NotEqualOperation,
    NotOperation,
    Operation,
    OrOperation,
    PowerOperation,
    ResolveVarOperation,
    StartsWithOperation,
    SubtractOperation,
    SumOperation,
    TernaryOperation,
    UnaryOperation,
)
from .query import Query
from .types import QueryResult

__all__ = [
    # Core classes
    "Query",
    "QueryEvaluator",
    # Base operation classes
    "Operation",
    "UnaryOperation",
    "BinaryOperation",
    "TernaryOperation",
    # Path resolution
    "ResolveVarOperation",
    # Arithmetic operations
    "AddOperation",
    "SubtractOperation",
    "MultiplyOperation",
    "DivideOperation",
    "ModuloOperation",
    "PowerOperation",
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
    # String operations
    "ContainsOperation",
    "StartsWithOperation",
    "EndsWithOperation",
    # Function operations
    "LengthOperation",
    "MaxOperation",
    "MinOperation",
    "SumOperation",
    "AnyOperation",
    "EveryOperation",
    "BoolOperation",
    "AbsOperation",
    "CountOperation",
    # Types and protocols
    "QueryResult",
    # Exceptions
    "QueryError",
    "QueryEvaluationError",
    "QueryOperationError",
    "QuerySyntaxError",
]
