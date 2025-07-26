"""
Query evaluation engine.

This module provides the core evaluation engine that executes
queries against tree data, handling caching and optimization.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .exceptions import OperandResolutionError, QueryEvaluationError
from .types import OperandProtocol, OperationProtocol, QueryProtocol, QueryResult

if TYPE_CHECKING:
    from ..tree import Tree

__all__ = [
    "QueryEvaluator",
]


class QueryEvaluator:
    """
    Basic query evaluator without caching.

    This evaluator handles the core logic of resolving operands
    and executing operations without any optimization.
    """

    def evaluate_query(
        self, query: QueryProtocol, tree: Tree, ctx: Any | None = None
    ) -> QueryResult:
        """
        Evaluate a query against tree data.

        Args:
            query: Query to evaluate
            tree: Tree instance
            ctx: Optional context

        Returns:
            Query result

        Raises:
            QueryEvaluationError: If evaluation fails
        """
        try:
            return query.evaluate(tree, ctx)
        except Exception as e:
            raise QueryEvaluationError("Query evaluation failed", original_error=e) from e

    def resolve_operand(self, operand: OperandProtocol, tree: Tree, ctx: Any | None = None) -> Any:
        """
        Resolve an operand to its value.

        Args:
            operand: Operand to resolve
            tree: Tree instance
            ctx: Optional context

        Returns:
            Resolved value

        Raises:
            OperandResolutionError: If resolution fails
        """
        try:
            return operand.resolve(tree, ctx, self)
        except Exception as e:
            if isinstance(e, OperandResolutionError):
                raise
            raise OperandResolutionError(
                "unknown", "Operand resolution failed", original_error=e
            ) from e

    def execute_operation(
        self, operation: OperationProtocol, left: Any, right: Any | None = None
    ) -> Any:
        """
        Execute an operation with operand values.

        Args:
            operation: Operation to execute
            left: Left operand value
            right: Right operand value (None for unary)

        Returns:
            Operation result

        Raises:
            QueryEvaluationError: If operation execution fails
        """
        try:
            return operation.execute(left, right, self)
        except Exception as e:
            raise QueryEvaluationError(
                f"Operation {operation.name} execution failed", original_error=e
            ) from e


# Default global evaluator instance
_default_evaluator = QueryEvaluator()


def get_default_evaluator() -> QueryEvaluator:
    """
    Get the default global evaluator instance.

    Returns:
        Default evaluator instance
    """
    return _default_evaluator


def set_default_evaluator(evaluator: QueryEvaluator) -> None:
    """
    Set the default global evaluator instance.

    Args:
        evaluator: New default evaluator
    """
    global _default_evaluator
    _default_evaluator = evaluator
