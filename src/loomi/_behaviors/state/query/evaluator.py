"""
Query evaluation engine.

This module provides the QueryEvaluator class that coordinates the evaluation
of query operation trees against tree data. It handles operand resolution
and delegates actual computation to the operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .exceptions import QueryEvaluationError
from .operations import Operation
from .query import Query

if TYPE_CHECKING:
    from ..path import Path
    from ..tree import Tree

__all__ = [
    "QueryEvaluator",
]


class QueryEvaluator:
    """
    Evaluates query operation trees against tree data.

    The QueryEvaluator serves as the coordinator between queries and tree data.
    It handles the evaluation of query operation trees by resolving operands
    and delegating calculations to the operations themselves.

    Key responsibilities:
    - Evaluate complete queries by starting from the root operation
    - Resolve operands (nested operations or literal values)
    - Handle path resolution using PathResolver
    - Provide consistent error handling and context management
    """

    def evaluate(self, query: Query, tree: "Tree", ctx: Any, /) -> Any:
        """
        Evaluate a complete query against tree data.

        This is the main entry point for query evaluation. It takes a query
        object and evaluates its operation tree against the provided tree data.

        Args:
            query: Query object containing the operation tree to evaluate
            tree: Tree instance providing data access
            ctx: Optional context (transaction/snapshot) for data operations

        Returns:
            Result of evaluating the query's operation tree

        Raises:
            QueryEvaluationError: If evaluation fails at any point

        Example:
            ```python
            evaluator = QueryEvaluator()

            # Evaluate simple query
            result = evaluator.evaluate(age_query, tree)

            # Evaluate with context
            with tree.transaction() as tx:
                result = evaluator.evaluate(complex_query, tree, ctx=tx)
            ```
        """
        try:
            return query.operations.calc(self, tree, ctx)
        except Exception as e:
            if isinstance(e, QueryEvaluationError):
                raise
            raise QueryEvaluationError(
                f"Failed to evaluate query: {query}", query=query, original_error=e
            ) from e

    def resolve_operand(self, operand: Operation | Any, tree: "Tree", ctx: Any) -> Any:
        """
        Resolve an operand to its actual value.

        Operands can be either nested operations (which need to be calculated)
        or literal values (which are returned as-is). This method handles
        the distinction and ensures proper evaluation.

        Args:
            operand: Operand to resolve - either an Operation or literal value
            tree: Tree instance for data access
            ctx: Optional context for operations

        Returns:
            Resolved value of the operand

        Raises:
            QueryEvaluationError: If operand resolution fails

        Example:
            ```python
            # Resolve nested operation
            result = evaluator.resolve_operand(add_operation, tree)

            # Resolve literal value
            result = evaluator.resolve_operand(42, tree)  # Returns 42
            ```
        """
        try:
            if isinstance(operand, Operation):
                # Operand is a nested operation - calculate it
                return operand.calc(self, tree, ctx)
            else:
                # Operand is a literal value - return as-is
                return operand
        except Exception as e:
            if isinstance(e, QueryEvaluationError):
                raise
            raise QueryEvaluationError(
                f"Failed to resolve operand: {operand}", original_error=e
            ) from e

    def resolve_path(self, path: Path, tree: "Tree", ctx: Any) -> Any:
        """
        Resolve a path to its value in the tree.

        This method uses the PathResolver to navigate through the tree
        structure and retrieve the actual value at the specified path.
        It serves as the bridge between the query system and path resolution.

        Args:
            path: Path object to resolve
            tree: Tree instance to resolve path against
            ctx: Optional context for path resolution

        Returns:
            Value at the path location in the tree

        Raises:
            QueryEvaluationError: If path resolution fails

        Example:
            ```python
            # Resolve path to actual value
            email = evaluator.resolve_path(email_path, tree)

            # Resolve with transaction context
            with tree.transaction() as tx:
                value = evaluator.resolve_path(config_path, tree, ctx=tx)
            ```
        """
        try:
            from ..path import PathResolver

            resolver = PathResolver()
            return resolver.resolve(path, tree, ctx)
        except Exception as e:
            raise QueryEvaluationError(f"Failed to resolve path: {path}", original_error=e) from e
