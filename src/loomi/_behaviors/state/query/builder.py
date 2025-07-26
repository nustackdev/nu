"""
QueryBuilder implementation for the query system.

This module provides the QueryBuilder class that enables natural Python
syntax for building queries through operator overloading and method chaining.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from .operands import FunctionOperand, LiteralOperand, PathOperand
from .operations import OPERATIONS
from .queries import OperationQuery, PathQuery
from .types import Path, QueryResult

if TYPE_CHECKING:
    from ..tree import Tree

__all__ = [
    "QueryBuilder",
]


class QueryBuilder:
    """
    Builder for creating queries using natural Python syntax.

    This class enables natural Python syntax for building queries:
    - Navigation: builder.users.alice.age
    - Indexing: builder.tasks[0]
    - Comparisons: builder.users.alice.age > 18
    - Operations: builder.users.alice.email.startswith("alice")

    All operations return Query objects that can be evaluated later.
    """

    def __init__(self, path: Path | None = None):
        """
        Initialize query builder.

        Args:
            path: Current path in the tree (empty for root)
        """
        self._path = path if path is not None else []

    # =========================================================================
    # NAVIGATION METHODS
    # =========================================================================

    def __getattr__(self, name: str) -> QueryBuilder:
        """
        Navigate to a child: builder.users -> navigate to 'users'

        Args:
            name: Child name to navigate to

        Returns:
            New QueryBuilder with extended path
        """
        if name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        return QueryBuilder(self._path + [name])

    def __getitem__(self, key: Union[int, str]) -> QueryBuilder:
        """
        Index access: builder.tasks[0] or builder.users["alice"]

        Args:
            key: Index or key to access

        Returns:
            New QueryBuilder with extended path
        """
        if isinstance(key, str):
            return QueryBuilder(self._path + [key])
        elif isinstance(key, int):
            return QueryBuilder(self._path + [str(key)])
        else:
            raise TypeError(f"Query indices must be strings or integers, not {type(key).__name__}")

    # =========================================================================
    # COMPARISON OPERATORS
    # =========================================================================

    def __gt__(self, other: Any) -> OperationQuery:
        """Greater than: builder.value > other"""
        return OperationQuery(
            left=PathOperand(self._path), operation=OPERATIONS["gt"], right=LiteralOperand(other)
        )

    def __lt__(self, other: Any) -> OperationQuery:
        """Less than: builder.value < other"""
        return OperationQuery(
            left=PathOperand(self._path), operation=OPERATIONS["lt"], right=LiteralOperand(other)
        )

    def __ge__(self, other: Any) -> OperationQuery:
        """Greater than or equal: builder.value >= other"""
        return OperationQuery(
            left=PathOperand(self._path), operation=OPERATIONS["ge"], right=LiteralOperand(other)
        )

    def __le__(self, other: Any) -> OperationQuery:
        """Less than or equal: builder.value <= other"""
        return OperationQuery(
            left=PathOperand(self._path), operation=OPERATIONS["le"], right=LiteralOperand(other)
        )

    def __eq__(self, other: Any) -> OperationQuery:
        """Equality: builder.value == other"""
        return OperationQuery(
            left=PathOperand(self._path), operation=OPERATIONS["eq"], right=LiteralOperand(other)
        )

    def __ne__(self, other: Any) -> OperationQuery:
        """Not equal: builder.value != other"""
        return OperationQuery(
            left=PathOperand(self._path), operation=OPERATIONS["ne"], right=LiteralOperand(other)
        )

    # =========================================================================
    # ARITHMETIC OPERATORS
    # =========================================================================

    def __add__(self, other: Any) -> OperationQuery:
        """Addition: builder.value + other"""
        return OperationQuery(
            left=PathOperand(self._path), operation=OPERATIONS["add"], right=LiteralOperand(other)
        )

    def __sub__(self, other: Any) -> OperationQuery:
        """Subtraction: builder.value - other"""
        return OperationQuery(
            left=PathOperand(self._path), operation=OPERATIONS["sub"], right=LiteralOperand(other)
        )

    def __mul__(self, other: Any) -> OperationQuery:
        """Multiplication: builder.value * other"""
        return OperationQuery(
            left=PathOperand(self._path), operation=OPERATIONS["mul"], right=LiteralOperand(other)
        )

    def __truediv__(self, other: Any) -> OperationQuery:
        """Division: builder.value / other"""
        return OperationQuery(
            left=PathOperand(self._path),
            operation=OPERATIONS["truediv"],
            right=LiteralOperand(other),
        )

    # =========================================================================
    # CONTAINMENT OPERATORS
    # =========================================================================

    def __contains__(self, item: Any) -> OperationQuery:
        """
        Containment check: item in builder.value

        Note: This creates builder.value.contains(item) due to Python's
        operator precedence with containment checks.
        """
        return OperationQuery(
            left=PathOperand(self._path),
            operation=OPERATIONS["contains"],
            right=LiteralOperand(item),
        )

    def contains(self, item: Any) -> OperationQuery:
        """
        Explicit containment check: builder.value.contains(item)

        Args:
            item: Item to check for containment

        Returns:
            OperationQuery for containment check
        """
        return OperationQuery(
            left=PathOperand(self._path),
            operation=OPERATIONS["contains"],
            right=LiteralOperand(item),
        )

    # =========================================================================
    # STRING METHODS
    # =========================================================================

    def startswith(self, prefix: str) -> OperationQuery:
        """
        String starts with check: builder.value.startswith(prefix)

        Args:
            prefix: Prefix to check for

        Returns:
            OperationQuery for startswith check
        """
        return OperationQuery(
            left=PathOperand(self._path),
            operation=OPERATIONS["startswith"],
            right=LiteralOperand(prefix),
        )

    def endswith(self, suffix: str) -> OperationQuery:
        """
        String ends with check: builder.value.endswith(suffix)

        Args:
            suffix: Suffix to check for

        Returns:
            OperationQuery for endswith check
        """
        return OperationQuery(
            left=PathOperand(self._path),
            operation=OPERATIONS["endswith"],
            right=LiteralOperand(suffix),
        )

    # =========================================================================
    # UNARY OPERATIONS
    # =========================================================================

    def length(self) -> OperationQuery:
        """
        Get length: len(builder.value)

        Returns:
            OperationQuery for length operation
        """
        return OperationQuery(left=PathOperand(self._path), operation=OPERATIONS["length"])

    def exists(self) -> OperationQuery:
        """
        Check existence: builder.value is not None

        Returns:
            OperationQuery for existence check
        """
        return OperationQuery(left=PathOperand(self._path), operation=OPERATIONS["exists"])

    # =========================================================================
    # FUNCTION OPERATIONS
    # =========================================================================

    def max(self) -> PathQuery:
        """Get maximum value from collection."""
        return PathQuery(FunctionOperand("max", PathOperand(self._path)))

    def min(self) -> PathQuery:
        """Get minimum value from collection."""
        return PathQuery(FunctionOperand("min", PathOperand(self._path)))

    def sum(self) -> PathQuery:
        """Get sum of collection."""
        return PathQuery(FunctionOperand("sum", PathOperand(self._path)))

    def sorted(self, reverse: bool = False) -> PathQuery:
        """Get sorted collection."""
        return PathQuery(FunctionOperand("sorted", PathOperand(self._path), reverse))

    # =========================================================================
    # VALUE EXTRACTION
    # =========================================================================

    def evaluate(self, tree: Tree, ctx: Any = None) -> QueryResult:
        """
        Evaluate as a path query (convenience method).

        This is equivalent to creating a PathQuery and evaluating it.

        Args:
            tree: Tree instance
            ctx: Optional context

        Returns:
            Value at this path
        """
        path_query = PathQuery(PathOperand(self._path))
        return path_query.evaluate(tree, ctx)

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def __repr__(self) -> str:
        """String representation for debugging."""
        if not self._path:
            return "QueryBuilder(root)"
        path_str = ".".join(self._path)
        return f"QueryBuilder({path_str})"

    def __bool__(self) -> bool:
        """
        Prevent accidental boolean evaluation.

        Raises:
            TypeError: Always, to prevent misuse
        """
        raise TypeError(
            "QueryBuilder objects cannot be used in boolean context. "
            "Use .evaluate(tree) to get the value, or comparison operators "
            "like > or == to create boolean queries."
        )

    @property
    def path(self) -> Path:
        """
        Get current path as a list.

        Returns:
            Copy of current path
        """
        return self._path.copy()
