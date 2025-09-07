"""
Query implementation for chainable operations.

This module provides the Query class that enables fluent, chainable operations
on paths through operator overloading. Queries are immutable and build operation
trees that can be evaluated against tree data.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

import attrs

from .exceptions import QueryEvaluationError
from .operations import (
    AbsOperation,
    AddOperation,
    AndOperation,
    AnyOperation,
    ArrayIndexOperation,
    BoolOperation,
    ContainsOperation,
    CountOperation,
    DecimalOperation,
    DictValueOperation,
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
    OrOperation,
    PowerOperation,
    ResolveVarOperation,
    StartsWithOperation,
    SubtractOperation,
    SumOperation,
)

if TYPE_CHECKING:
    from ..path import _Path
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
    def create(cls, path: _Path) -> Query:
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
    # UTILITY METHODS
    # =========================================================================

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

    def evaluate(self, tree: "Tree", ctx: Any, vars: dict[str | int, Any]) -> Any:
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
                result = query.evaluate(tree, ctx=tx, vars=vars)
            ```
        """
        try:
            return self.operations.calc(tree, ctx, vars)
        except Exception as e:
            if isinstance(e, QueryEvaluationError):
                raise
            raise QueryEvaluationError(
                f"Failed to evaluate query: {self}", query=self, original_error=e
            ) from e

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

    def __mod__(self, other: Any) -> Query:
        """
        Modulo: query % other

        Args:
            other: Value to get modulo with

        Returns:
            New Query with modulo operation
        """
        other_ops = other.operations if isinstance(other, Query) else other
        return Query(operations=ModuloOperation(left=self.operations, right=other_ops))

    def __pow__(self, other: Any) -> Query:
        """
        Power: query ** other

        Args:
            other: Exponent value

        Returns:
            New Query with power operation
        """
        other_ops = other.operations if isinstance(other, Query) else other
        return Query(operations=PowerOperation(left=self.operations, right=other_ops))

    def __abs__(self) -> Query:
        """
        Absolute value: abs(query)

        Returns:
            New Query with abs operation

        Example:
            ```python
            result = abs(query)
            ```
        """
        return Query(operations=AbsOperation(operand=self.operations))

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

    def and_(self, other: Any) -> Query:
        """
        Logical AND: query.and_(other)

        Args:
            other: Value to AND with (can be another Query)

        Returns:
            New Query with AND operation
        """
        other_ops = other.operations if isinstance(other, Query) else other
        return Query(operations=AndOperation(left=self.operations, right=other_ops))

    def or_(self, other: Any) -> Query:
        """
        Logical OR: query.or_(other)

        Args:
            other: Value to OR with (can be another Query)

        Returns:
            New Query with OR operation
        """
        other_ops = other.operations if isinstance(other, Query) else other
        return Query(operations=OrOperation(left=self.operations, right=other_ops))

    def eq(self, other: Any) -> Query:
        """
        Equality: query.eq(other)

        Args:
            other: Value to compare against

        Returns:
            New Query with equality operation
        """
        other_ops = other.operations if isinstance(other, Query) else other
        return Query(operations=EqualOperation(left=self.operations, right=other_ops))

    def not_(self) -> Query:
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

    def any(self) -> Query:
        """
        Any: query.any() - returns True if any element is truthy

        Returns:
            New Query with any operation
        """
        return Query(operations=AnyOperation(operand=self.operations))

    def every(self) -> Query:
        """
        Every: query.every() - returns True if all elements are truthy

        Returns:
            New Query with every operation
        """
        return Query(operations=EveryOperation(operand=self.operations))

    def all(self) -> Query:
        """
        All: query.all() - alias for every()

        Returns:
            New Query with every operation
        """
        return Query(operations=EveryOperation(operand=self.operations))

    def count(self) -> Query:
        """
        Count: query.count() - count non-None values

        Returns:
            New Query with count operation
        """
        return Query(operations=CountOperation(operand=self.operations))

    def bool(self) -> Query:
        """
        Boolean conversion: bool(query)

        Returns:
            New Query with bool operation

        Example:
            ```python
            result = query.bool()
            ```
        """
        return Query(operations=BoolOperation(operand=self.operations))

    # -------
    # custom (tmp, to remove)
    # -------

    def to_dec(self) -> Query:
        """
        Convert query to Decimal.

        Returns:
            New Query with Decimal conversion

        Example:
            ```python
            result = query.to_dec()
            ```
        """
        return Query(operations=DecimalOperation(operand=self.operations))

    def get_arr_index(self, arr: Any) -> Query:
        """
        Get array index: query.get_arr_index()

        Returns:
            New Query with array index operation
        """
        from ..path import Path

        if isinstance(arr, Path):
            return Query(
                operations=ArrayIndexOperation(left=self.operations, right=ResolveVarOperation(arr))
            )
        elif isinstance(arr, Query):
            return Query(operations=ArrayIndexOperation(left=self.operations, right=arr.operations))
        return Query(operations=ArrayIndexOperation(left=self.operations, right=arr))

    def get_dict_value(self, key: Any) -> Query:
        """
        Get dictionary value: query.get_dict_value()

        Returns:
            New Query with dictionary value operation
        """
        from ..path import Path

        if isinstance(key, Path):
            return Query(
                operations=DictValueOperation(left=self.operations, right=ResolveVarOperation(key))
            )
        elif isinstance(key, Query):
            return Query(operations=DictValueOperation(left=self.operations, right=key.operations))
        return Query(operations=DictValueOperation(left=self.operations, right=key))
