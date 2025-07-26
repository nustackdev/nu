"""
Type definitions and protocols for the query system.

This module defines the core types and protocols used throughout
the query system, establishing interfaces without implementation details.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, TypeVar

if TYPE_CHECKING:
    from ..tree import Tree

__all__ = [
    "QueryProtocol",
    "OperationProtocol",
    "OperandProtocol",
    "EvaluatorProtocol",
    "QueryResult",
    "PathComponent",
    "PathList",
    "OperationT",
    "OperandT",
]

# Type variables
OperationT = TypeVar("OperationT", bound="OperationProtocol")
OperandT = TypeVar("OperandT", bound="OperandProtocol")

# Basic types
PathComponent = str
PathList = list[PathComponent]
QueryResult = Any


class QueryProtocol(Protocol):
    """Base protocol for all query types."""

    def evaluate(self, tree: Tree, ctx: Any = None) -> QueryResult:
        """
        Evaluate query against tree data.

        Args:
            tree: Tree instance to query against
            ctx: Optional context (transaction/snapshot)

        Returns:
            Query result
        """
        ...


class OperationProtocol(Protocol):
    """Protocol for operation implementations."""

    @property
    def name(self) -> str:
        """Operation name for registry."""
        ...

    @property
    def is_unary(self) -> bool:
        """Whether this is a unary operation (single operand)."""
        ...

    def execute(
        self, left: Any, right: Any = None, evaluator: EvaluatorProtocol | None = None
    ) -> Any:
        """
        Execute operation with given operands.

        Args:
            left: Left operand value
            right: Right operand value (None for unary operations)
            evaluator: Evaluator instance for nested evaluation

        Returns:
            Operation result
        """
        ...


class OperandProtocol(Protocol):
    """Protocol for operand implementations."""

    def resolve(
        self, tree: Tree, ctx: Any = None, evaluator: EvaluatorProtocol | None = None
    ) -> Any:
        """
        Resolve operand to actual value.

        Args:
            tree: Tree instance to resolve against
            ctx: Optional context (transaction/snapshot)
            evaluator: Evaluator instance for nested resolution

        Returns:
            Resolved value
        """
        ...


class EvaluatorProtocol(Protocol):
    """Protocol for query evaluator implementations."""

    def evaluate_query(self, query: QueryProtocol, tree: Tree, ctx: Any = None) -> QueryResult:
        """
        Evaluate a query against tree data.

        Args:
            query: Query to evaluate
            tree: Tree instance
            ctx: Optional context

        Returns:
            Query result
        """
        ...

    def resolve_operand(self, operand: OperandProtocol, tree: Tree, ctx: Any = None) -> Any:
        """
        Resolve an operand to its value.

        Args:
            operand: Operand to resolve
            tree: Tree instance
            ctx: Optional context

        Returns:
            Resolved value
        """
        ...

    def execute_operation(self, operation: OperationProtocol, left: Any, right: Any = None) -> Any:
        """
        Execute an operation with operand values.

        Args:
            operation: Operation to execute
            left: Left operand value
            right: Right operand value (None for unary)

        Returns:
            Operation result
        """
        ...
