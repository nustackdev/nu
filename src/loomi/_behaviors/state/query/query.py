"""
Query implementation for chainable operations.

This module provides the Query class that enables fluent, chainable operations
on paths through operator overloading. Queries are immutable and build operation
trees that can be evaluated against tree data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import attrs

from .operations import (
    AddOperation,
    AndOperation,
    ContainsOperation,
    DivideOperation,
    EndsWithOperation,
    EqualOperation,
    GreaterEqualOperation,
    GreaterThanOperation,
    LengthOperation,
    LessEqualOperation,
    LessThanOperation,
    MaxOperation,
    MinOperation,
    MultiplyOperation,
    NotEqualOperation,
    NotOperation,
    OrOperation,
    ResolveVarOperation,
    StartsWithOperation,
    SubtractOperation,
    SumOperation,
)

if TYPE_CHECKING:
    from ..path import Path
    from ..tree import Tree
    from .operations import Operation

__all__ = [
    "Query",
]


@attrs.define(frozen=True)
class Query:
    """
    Immutable query object that enables chainable operations.

    Query objects track operations through an operation tree, where each
    operation can contain nested operations or literal values. All operations
    return new Query objects, enabling unlimited chaining.

    Example:
        ```python
        # Create query from path
        query = tree.P.users.alice.age.Q()

        # Chain operations
        result = (query + 10 + 5 > 18 and
                 tree.P.users.alice.status.Q() == "active")

        # Evaluate against tree
        is_valid = result.evaluate(tree)
        ```
    """

    operations: Operation = attrs.field()

    # =========================================================================
    # FACTORY METHODS
    # =========================================================================

    @classmethod
    def create(cls, path: Path) -> Query:
        """
        Create query from path.

        Wraps the path in a ResolveVarOperation for consistency - everything
        in the query system is an operation.

        Args:
            path: Path object to create query from

        Returns:
            New Query with path as root operation

        Example:
            ```python
            query = Query.create(tree.P.users.alice.age)
            ```
        """
        return cls(operations=ResolveVarOperation(operand=path))

    # =========================================================================
    # ARITHMETIC OPERATIONS
    # =========================================================================

    def __add__(self, other: Any) -> Query:
        """
        Addition: query + other

        Args:
            other: Value to add (can be literal or another Query)

        Returns:
            New Query with addition operation

        Example:
            ```python
            result = query + 10
            result = query + other_query
            ```
        """
        other_ops = other.operations if isinstance(other, Query) else other
        return Query(operations=AddOperation(left=self.operations, right=other_ops))

    def __radd__(self, other: Any) -> Query:
        """Reverse addition: other + query"""
        return Query(operations=AddOperation(left=other, right=self.operations))

    def __sub__(self, other: Any) -> Query:
        """
        Subtraction: query - other

        Args:
            other: Value to subtract

        Returns:
            New Query with subtraction operation
        """
        other_ops = other.operations if isinstance(other, Query) else other
        return Query(operations=SubtractOperation(left=self.operations, right=other_ops))

    def __rsub__(self, other: Any) -> Query:
        """Reverse subtraction: other - query"""
        return Query(operations=SubtractOperation(left=other, right=self.operations))

    def __mul__(self, other: Any) -> Query:
        """
        Multiplication: query * other

        Args:
            other: Value to multiply by

        Returns:
            New Query with multiplication operation
        """
        other_ops = other.operations if isinstance(other, Query) else other
        return Query(operations=MultiplyOperation(left=self.operations, right=other_ops))

    def __rmul__(self, other: Any) -> Query:
        """Reverse multiplication: other * query"""
        return Query(operations=MultiplyOperation(left=other, right=self.operations))

    def __truediv__(self, other: Any) -> Query:
        """
        Division: query / other

        Args:
            other: Value to divide by

        Returns:
            New Query with division operation
        """
        other_ops = other.operations if isinstance(other, Query) else other
        return Query(operations=DivideOperation(left=self.operations, right=other_ops))

    def __rtruediv__(self, other: Any) -> Query:
        """Reverse division: other / query"""
        return Query(operations=DivideOperation(left=other, right=self.operations))

    # =========================================================================
    # COMPARISON OPERATIONS
    # =========================================================================

    def __gt__(self, other: Any) -> Query:
        """
        Greater than: query > other

        Args:
            other: Value to compare against

        Returns:
            New Query with greater than operation
        """
        other_ops = other.operations if isinstance(other, Query) else other
        return Query(operations=GreaterThanOperation(left=self.operations, right=other_ops))

    def __lt__(self, other: Any) -> Query:
        """
        Less than: query < other

        Args:
            other: Value to compare against

        Returns:
            New Query with less than operation
        """
        other_ops = other.operations if isinstance(other, Query) else other
        return Query(operations=LessThanOperation(left=self.operations, right=other_ops))

    def __ge__(self, other: Any) -> Query:
        """
        Greater than or equal: query >= other

        Args:
            other: Value to compare against

        Returns:
            New Query with greater than or equal operation
        """
        other_ops = other.operations if isinstance(other, Query) else other
        return Query(operations=GreaterEqualOperation(left=self.operations, right=other_ops))

    def __le__(self, other: Any) -> Query:
        """
        Less than or equal: query <= other

        Args:
            other: Value to compare against

        Returns:
            New Query with less than or equal operation
        """
        other_ops = other.operations if isinstance(other, Query) else other
        return Query(operations=LessEqualOperation(left=self.operations, right=other_ops))

    def __eq__(self, other: Any) -> Query:
        """
        Equality: query == other

        Args:
            other: Value to compare against

        Returns:
            New Query with equality operation

        Note:
            This overrides object equality. Use is_equal_query() for Query comparison.
        """
        other_ops = other.operations if isinstance(other, Query) else other
        return Query(operations=EqualOperation(left=self.operations, right=other_ops))

    def __ne__(self, other: Any) -> Query:
        """
        Not equal: query != other

        Args:
            other: Value to compare against

        Returns:
            New Query with not equal operation
        """
        other_ops = other.operations if isinstance(other, Query) else other
        return Query(operations=NotEqualOperation(left=self.operations, right=other_ops))

    # =========================================================================
    # LOGICAL OPERATIONS
    # =========================================================================

    def __and__(self, other: Any) -> Query:
        """
        Logical AND: query & other or query and other

        Args:
            other: Query or value to combine with AND

        Returns:
            New Query with AND operation

        Example:
            ```python
            result = (query1 & query2)
            result = query1.__and__(query2)
            ```
        """
        other_ops = other.operations if isinstance(other, Query) else other
        return Query(operations=AndOperation(left=self.operations, right=other_ops))

    def __rand__(self, other: Any) -> Query:
        """Reverse logical AND: other & query"""
        return Query(operations=AndOperation(left=other, right=self.operations))

    def __or__(self, other: Any) -> Query:
        """
        Logical OR: query | other or query or other

        Args:
            other: Query or value to combine with OR

        Returns:
            New Query with OR operation
        """
        other_ops = other.operations if isinstance(other, Query) else other
        return Query(operations=OrOperation(left=self.operations, right=other_ops))

    def __ror__(self, other: Any) -> Query:
        """Reverse logical OR: other | query"""
        return Query(operations=OrOperation(left=other, right=self.operations))

    def __invert__(self) -> Query:
        """
        Logical NOT: ~query or not query

        Returns:
            New Query with NOT operation

        Example:
            ```python
            result = ~query
            result = query.__invert__()
            ```
        """
        return Query(operations=NotOperation(operand=self.operations))

    # =========================================================================
    # STRING OPERATIONS
    # =========================================================================

    def __contains__(self, item: Any) -> Query:
        """
        Contains check: item in query

        Args:
            item: Item to check for containment

        Returns:
            New Query with contains operation

        Note:
            Due to Python semantics, this creates query.contains(item)
        """
        return Query(operations=ContainsOperation(left=self.operations, right=item))

    def contains(self, item: Any) -> Query:
        """
        Explicit contains check: query.contains(item)

        Args:
            item: Item to check for containment

        Returns:
            New Query with contains operation
        """
        return Query(operations=ContainsOperation(left=self.operations, right=item))

    def startswith(self, prefix: str) -> Query:
        """
        String starts with: query.startswith(prefix)

        Args:
            prefix: Prefix to check for

        Returns:
            New Query with startswith operation
        """
        return Query(operations=StartsWithOperation(left=self.operations, right=prefix))

    def endswith(self, suffix: str) -> Query:
        """
        String ends with: query.endswith(suffix)

        Args:
            suffix: Suffix to check for

        Returns:
            New Query with endswith operation
        """
        return Query(operations=EndsWithOperation(left=self.operations, right=suffix))

    # =========================================================================
    # FUNCTION OPERATIONS
    # =========================================================================

    def __len__(self) -> Query:
        """
        Length: len(query)

        Returns:
            New Query with length operation
        """
        return Query(operations=LengthOperation(operand=self.operations))

    def length(self) -> Query:
        """
        Explicit length: query.length()

        Returns:
            New Query with length operation
        """
        return Query(operations=LengthOperation(operand=self.operations))

    def max(self) -> Query:
        """
        Maximum: query.max()

        Returns:
            New Query with max operation
        """
        return Query(operations=MaxOperation(operand=self.operations))

    def min(self) -> Query:
        """
        Minimum: query.min()

        Returns:
            New Query with min operation
        """
        return Query(operations=MinOperation(operand=self.operations))

    def sum(self) -> Query:
        """
        Sum: query.sum()

        Returns:
            New Query with sum operation
        """
        return Query(operations=SumOperation(operand=self.operations))

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def is_equal_query(self, other: Query) -> bool:
        """
        Check if two queries have the same operations.

        Args:
            other: Other query to compare with

        Returns:
            True if queries have identical operation trees

        Note:
            Use this instead of == which creates an EqualOperation
        """
        return isinstance(other, Query) and self.operations == other.operations

    def __repr__(self) -> str:
        """
        Debug representation showing operation tree.

        Returns:
            String representation for debugging
        """
        return f"Query({self.operations})"

    def __hash__(self) -> int:
        """
        Hash based on operations tree.

        Returns:
            Hash value for use in sets/dicts
        """
        return hash(self.operations)

    # =========================================================================
    # EVALUATION
    # =========================================================================

    def evaluate(self, tree: "Tree", ctx: Any = None) -> Any:
        """
        Evaluate the query against a tree.

        This resolves the operation tree and returns the final result.
        If ctx is provided, it will be used for data access.

        Args:
            tree: Tree instance to evaluate against
            ctx: Optional context (transaction/snapshot) for data operations

        Returns:
            Result of evaluating the query's operation tree

        Raises:
            QueryEvaluationError: If evaluation fails at any point

        Example:
            ```python
            result = query.evaluate(tree)
            with tree.transaction() as tx:
                result = query.evaluate(tree, ctx=tx)
            ```
        """
        from .evaluator import QueryEvaluator

        evaluator = QueryEvaluator()
        return evaluator.evaluate(self, tree, ctx=ctx)
