"""
Query implementations for the query system.

This module provides the core query types that can be evaluated
against tree data to produce results.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from .exceptions import QueryEvaluationError
from .types import OperandProtocol, OperationProtocol, QueryResult

if TYPE_CHECKING:
    from ..tree import Tree

__all__ = [
    "Query",
    "PathQuery",
    "OperationQuery",
]


class Query(ABC):
    """
    Base class for all query implementations.

    Queries are immutable objects that represent a complete query
    that can be evaluated against tree data to produce a result.
    """

    @abstractmethod
    def evaluate(self, tree: Tree, ctx: Any = None) -> QueryResult:
        """
        Evaluate this query against the provided tree.

        Args:
            tree: Tree instance to query against
            ctx: Optional context (transaction/snapshot)

        Returns:
            Query evaluation result

        Raises:
            QueryEvaluationError: If evaluation fails
        """
        pass

    def __eq__(self, other: object) -> bool:
        """Default equality based on class and attributes."""
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __hash__(self) -> int:
        """Default hash based on class and hashable attributes."""
        hashable_attrs = tuple(
            v
            for v in self.__dict__.values()
            if isinstance(v, (str, int, float, bool, tuple, type(None)))
        )
        return hash((self.__class__, hashable_attrs))


class PathQuery(Query):
    """
    A query that extracts a value from a path in the tree.

    This represents simple path navigation like builder.users.alice.age
    and returns the actual value at that path.
    """

    def __init__(self, operand: OperandProtocol):
        """
        Initialize path query.

        Args:
            operand: Operand to extract value from (typically PathOperand)
        """
        self.operand = operand

    def evaluate(self, tree: Tree, ctx: Any = None) -> QueryResult:
        """
        Evaluate by resolving the operand to get the path value.

        Args:
            tree: Tree instance
            ctx: Optional context

        Returns:
            Value at the path
        """
        from .evaluator import get_default_evaluator  # Avoid circular import

        evaluator = get_default_evaluator()

        try:
            return evaluator.resolve_operand(self.operand, tree, ctx)
        except Exception as e:
            raise QueryEvaluationError("Failed to evaluate path query", original_error=e) from e

    def __repr__(self) -> str:
        return f"PathQuery({self.operand})"


class OperationQuery(Query):
    """
    A query that represents an operation between operands.

    This captures operations like comparisons (age > 18), arithmetic (x + y),
    logical operations (a & b), etc. and evaluates them when requested.
    """

    def __init__(
        self,
        left: OperandProtocol,
        operation: OperationProtocol,
        right: OperandProtocol | None = None,
    ):
        """
        Initialize operation query.

        Args:
            left: Left operand
            operation: Operation to apply
            right: Right operand (None for unary operations)
        """
        self.left = left
        self.operation = operation
        self.right = right

        # Validate operation arity
        if operation.is_unary and right is not None:
            raise ValueError(f"Unary operation {operation.name} cannot have right operand")
        if not operation.is_unary and right is None:
            raise ValueError(f"Binary operation {operation.name} requires right operand")

    def evaluate(self, tree: Tree, ctx: Any = None) -> QueryResult:
        """
        Evaluate the operation query.

        Args:
            tree: Tree instance
            ctx: Optional context

        Returns:
            Operation result
        """
        from .evaluator import get_default_evaluator  # Avoid circular import

        evaluator = get_default_evaluator()

        try:
            # Resolve operands
            left_value = evaluator.resolve_operand(self.left, tree, ctx)
            right_value = evaluator.resolve_operand(self.right, tree, ctx) if self.right else None

            # Execute operation
            return evaluator.execute_operation(self.operation, left_value, right_value)

        except Exception as e:
            raise QueryEvaluationError(
                f"Failed to evaluate operation query: {self.operation.name}", original_error=e
            ) from e

    # =========================================================================
    # LOGICAL OPERATIONS FOR CHAINING OPERATION QUERIES
    # =========================================================================

    def __and__(self, other: OperationQuery) -> OperationQuery:
        """
        Logical AND: operation1 & operation2

        Args:
            other: Other OperationQuery to combine with

        Returns:
            New OperationQuery representing the AND operation
        """
        from .operands import QueryOperand  # Avoid circular import
        from .operations import OPERATIONS

        return OperationQuery(
            left=QueryOperand(self), operation=OPERATIONS["and"], right=QueryOperand(other)
        )

    def __or__(self, other: OperationQuery) -> OperationQuery:
        """
        Logical OR: operation1 | operation2

        Args:
            other: Other OperationQuery to combine with

        Returns:
            New OperationQuery representing the OR operation
        """
        from .operands import QueryOperand  # Avoid circular import
        from .operations import OPERATIONS

        return OperationQuery(
            left=QueryOperand(self), operation=OPERATIONS["or"], right=QueryOperand(other)
        )

    def __invert__(self) -> OperationQuery:
        """
        Logical NOT: ~operation

        Returns:
            New OperationQuery representing the NOT operation
        """
        from .operands import QueryOperand  # Avoid circular import
        from .operations import OPERATIONS

        return OperationQuery(left=QueryOperand(self), operation=OPERATIONS["not"])

    def __repr__(self) -> str:
        if self.operation.is_unary:
            return f"OperationQuery({self.operation.name} {self.left})"
        return f"OperationQuery({self.left} {self.operation.name} {self.right})"
