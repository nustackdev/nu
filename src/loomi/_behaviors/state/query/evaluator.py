"""
Query evaluation engine.

This module provides the core evaluation engine that executes
queries against tree data, handling caching and optimization.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Tuple
from weakref import WeakKeyDictionary

from .exceptions import CacheError, OperandResolutionError, QueryEvaluationError
from .types import OperandProtocol, OperationProtocol, QueryProtocol, QueryResult

if TYPE_CHECKING:
    from ..tree import Tree

__all__ = [
    "QueryEvaluator",
    "CachingQueryEvaluator",
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


class CachingQueryEvaluator(QueryEvaluator):
    """
    Caching query evaluator with performance optimizations.

    This evaluator caches results to avoid repeated computations
    and provides better performance for complex or repeated queries.
    """

    def __init__(self):
        """Initialize caching evaluator."""
        # Use weak references to avoid memory leaks
        # Cache key: (query_id, tree_id, ctx_id) -> result
        self._query_cache: WeakKeyDictionary = WeakKeyDictionary()
        # Cache key: (operand_id, tree_id, ctx_id) -> value
        self._operand_cache: WeakKeyDictionary = WeakKeyDictionary()
        # Cache key: (operation_name, left_value, right_value) -> result
        self._operation_cache: Dict[Tuple, Any] = {}

        # Cache statistics for debugging/monitoring
        self._stats = {
            "query_hits": 0,
            "query_misses": 0,
            "operand_hits": 0,
            "operand_misses": 0,
            "operation_hits": 0,
            "operation_misses": 0,
        }

    def evaluate_query(
        self, query: QueryProtocol, tree: Tree, ctx: Any | None = None
    ) -> QueryResult:
        """
        Evaluate query with caching.

        Args:
            query: Query to evaluate
            tree: Tree instance
            ctx: Optional context

        Returns:
            Cached or computed query result
        """
        # Create cache key
        cache_key = (id(query), id(tree), id(ctx))

        # Check cache
        try:
            if tree in self._query_cache:
                tree_cache = self._query_cache[tree]
                if cache_key in tree_cache:
                    self._stats["query_hits"] += 1
                    return tree_cache[cache_key]
        except Exception as e:
            # Cache lookup failed, continue with computation
            raise CacheError(f"Query cache lookup failed: {e}") from e

        # Cache miss - compute result
        self._stats["query_misses"] += 1
        try:
            result = super().evaluate_query(query, tree, ctx)

            # Store in cache
            if tree not in self._query_cache:
                self._query_cache[tree] = {}
            self._query_cache[tree][cache_key] = result

            return result

        except Exception:
            # Don't cache exceptions
            raise

    def resolve_operand(self, operand: OperandProtocol, tree: Tree, ctx: Any | None = None) -> Any:
        """
        Resolve operand with caching.

        Args:
            operand: Operand to resolve
            tree: Tree instance
            ctx: Optional context

        Returns:
            Cached or computed operand value
        """
        # Create cache key
        cache_key = (id(operand), id(tree), id(ctx))

        # Check cache
        try:
            if tree in self._operand_cache:
                tree_cache = self._operand_cache[tree]
                if cache_key in tree_cache:
                    self._stats["operand_hits"] += 1
                    return tree_cache[cache_key]
        except Exception as e:
            # Cache lookup failed, continue with computation
            raise CacheError(f"Operand cache lookup failed: {e}") from e

        # Cache miss - compute result
        self._stats["operand_misses"] += 1
        try:
            result = super().resolve_operand(operand, tree, ctx)

            # Store in cache
            if tree not in self._operand_cache:
                self._operand_cache[tree] = {}
            self._operand_cache[tree][cache_key] = result

            return result

        except Exception:
            # Don't cache exceptions
            raise

    def execute_operation(
        self, operation: OperationProtocol, left: Any, right: Any | None = None
    ) -> Any:
        """
        Execute operation with caching.

        Args:
            operation: Operation to execute
            left: Left operand value
            right: Right operand value (None for unary)

        Returns:
            Cached or computed operation result
        """
        # Create cache key for hashable values only
        try:
            if right is None:
                cache_key = (operation.name, left)
            else:
                cache_key = (operation.name, left, right)

            # Try to hash the key to ensure it's cacheable
            hash(cache_key)

            # Check cache
            if cache_key in self._operation_cache:
                self._stats["operation_hits"] += 1
                return self._operation_cache[cache_key]

        except TypeError:
            # Values not hashable - skip caching
            return super().execute_operation(operation, left, right)

        # Cache miss - compute result
        self._stats["operation_misses"] += 1
        try:
            result = super().execute_operation(operation, left, right)

            # Store in cache (only if hashable)
            try:
                self._operation_cache[cache_key] = result
            except TypeError:
                # Result not hashable - don't cache
                pass

            return result

        except Exception:
            # Don't cache exceptions
            raise

    def clear_cache(self) -> None:
        """Clear all caches."""
        self._query_cache.clear()
        self._operand_cache.clear()
        self._operation_cache.clear()

        # Reset statistics
        for key in self._stats:
            self._stats[key] = 0

    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache performance statistics.

        Returns:
            Dictionary with cache hit/miss counts
        """
        return self._stats.copy()

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get detailed cache information.

        Returns:
            Dictionary with cache sizes and statistics
        """
        return {
            "stats": self.get_cache_stats(),
            "query_cache_size": len(self._query_cache),
            "operand_cache_size": len(self._operand_cache),
            "operation_cache_size": len(self._operation_cache),
        }


# Default global evaluator instance
_default_evaluator = CachingQueryEvaluator()


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
