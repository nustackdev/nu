"""
LazyQuery implementation for the query system.

This module provides the LazyQuery class that enables natural Python
syntax for building queries through operator overloading and method chaining.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from .core import LazyOperation, ValueQuery
from .operands import FunctionOperand, LiteralOperand, PathOperand
from .operations import OPERATIONS
from .types import PathList, QueryResult

if TYPE_CHECKING:
    from ..tree import Tree

__all__ = [
    "LazyQuery",
]


class LazyQuery:
    """
    Lazy query that captures operations without immediate execution.

    This class enables natural Python syntax for building queries:
    - Navigation: query.users.alice.age
    - Indexing: query.tasks[0]
    - Comparisons: query.users.alice.age > 18
    - Operations: query.users.alice.email.startswith("alice")

    All operations are captured lazily and only executed when evaluate() is called.
    """

    def __init__(self, path: PathList = None):
        """
        Initialize lazy query.

        Args:
            path: Current path in the tree (empty for root)
        """
        self._path = path if path is not None else []

    # =========================================================================
    # NAVIGATION METHODS
    # =========================================================================

    def __getattr__(self, name: str) -> LazyQuery:
        """
        Navigate to a child: query.users -> navigate to 'users'

        Args:
            name: Child name to navigate to

        Returns:
            New LazyQuery with extended path
        """
        if name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        return LazyQuery(self._path + [name])

    def __getitem__(self, key: Union[int, str]) -> LazyQuery:
        """
        Index access: query.tasks[0] or query.users["alice"]

        Args:
            key: Index or key to access

        Returns:
            New LazyQuery with extended path
        """
        if isinstance(key, str):
            return LazyQuery(self._path + [key])
        elif isinstance(key, int):
            return LazyQuery(self._path + [str(key)])
        else:
            raise TypeError(f"Query indices must be strings or integers, not {type(key).__name__}")

    # =========================================================================
    # COMPARISON OPERATORS
    # =========================================================================

    def __gt__(self, other: Any) -> LazyOperation:
        """Greater than: query.value > other"""
        return LazyOperation(
            left=PathOperand(self._path), operation=OPERATIONS["gt"], right=LiteralOperand(other)
        )

    def __lt__(self, other: Any) -> LazyOperation:
        """Less than: query.value < other"""
        return LazyOperation(
            left=PathOperand(self._path), operation=OPERATIONS["lt"], right=LiteralOperand(other)
        )

    def __ge__(self, other: Any) -> LazyOperation:
        """Greater than or equal: query.value >= other"""
        return LazyOperation(
            left=PathOperand(self._path), operation=OPERATIONS["ge"], right=LiteralOperand(other)
        )

    def __le__(self, other: Any) -> LazyOperation:
        """Less than or equal: query.value <= other"""
        return LazyOperation(
            left=PathOperand(self._path), operation=OPERATIONS["le"], right=LiteralOperand(other)
        )

    def __eq__(self, other: Any) -> LazyOperation:
        """Equality: query.value == other"""
        return LazyOperation(
            left=PathOperand(self._path), operation=OPERATIONS["eq"], right=LiteralOperand(other)
        )

    def __ne__(self, other: Any) -> LazyOperation:
        """Not equal: query.value != other"""
        return LazyOperation(
            left=PathOperand(self._path), operation=OPERATIONS["ne"], right=LiteralOperand(other)
        )

    # =========================================================================
    # ARITHMETIC OPERATORS
    # =========================================================================

    def __add__(self, other: Any) -> LazyOperation:
        """Addition: query.value + other"""
        return LazyOperation(
            left=PathOperand(self._path), operation=OPERATIONS["add"], right=LiteralOperand(other)
        )

    def __sub__(self, other: Any) -> LazyOperation:
        """Subtraction: query.value - other"""
        return LazyOperation(
            left=PathOperand(self._path), operation=OPERATIONS["sub"], right=LiteralOperand(other)
        )

    def __mul__(self, other: Any) -> LazyOperation:
        """Multiplication: query.value * other"""
        return LazyOperation(
            left=PathOperand(self._path), operation=OPERATIONS["mul"], right=LiteralOperand(other)
        )

    def __truediv__(self, other: Any) -> LazyOperation:
        """Division: query.value / other"""
        return LazyOperation(
            left=PathOperand(self._path),
            operation=OPERATIONS["truediv"],
            right=LiteralOperand(other),
        )

    # =========================================================================
    # CONTAINMENT OPERATORS
    # =========================================================================

    def __contains__(self, item: Any) -> LazyOperation:
        """
        Containment check: item in query.value

        Note: This creates query.value.contains(item) due to Python's
        operator precedence with containment checks.
        """
        return LazyOperation(
            left=PathOperand(self._path),
            operation=OPERATIONS["contains"],
            right=LiteralOperand(item),
        )

    def contains(self, item: Any) -> LazyOperation:
        """
        Explicit containment check: query.value.contains(item)

        Args:
            item: Item to check for containment

        Returns:
            LazyOperation for containment check
        """
        return LazyOperation(
            left=PathOperand(self._path),
            operation=OPERATIONS["contains"],
            right=LiteralOperand(item),
        )

    # =========================================================================
    # STRING METHODS
    # =========================================================================

    def startswith(self, prefix: str) -> LazyOperation:
        """
        String starts with check: query.value.startswith(prefix)

        Args:
            prefix: Prefix to check for

        Returns:
            LazyOperation for startswith check
        """
        return LazyOperation(
            left=PathOperand(self._path),
            operation=OPERATIONS["startswith"],
            right=LiteralOperand(prefix),
        )

    def endswith(self, suffix: str) -> LazyOperation:
        """
        String ends with check: query.value.endswith(suffix)

        Args:
            suffix: Suffix to check for

        Returns:
            LazyOperation for endswith check
        """
        return LazyOperation(
            left=PathOperand(self._path),
            operation=OPERATIONS["endswith"],
            right=LiteralOperand(suffix),
        )

    # =========================================================================
    # UNARY OPERATIONS
    # =========================================================================

    def length(self) -> LazyOperation:
        """
        Get length: len(query.value)

        Returns:
            LazyOperation for length operation
        """
        return LazyOperation(left=PathOperand(self._path), operation=OPERATIONS["length"])

    def exists(self) -> LazyOperation:
        """
        Check existence: query.value is not None

        Returns:
            LazyOperation for existence check
        """
        return LazyOperation(left=PathOperand(self._path), operation=OPERATIONS["exists"])

    # =========================================================================
    # FUNCTION OPERATIONS
    # =========================================================================

    def max(self) -> LazyOperation:
        """Get maximum value from collection."""
        return LazyOperation(
            left=FunctionOperand("max", PathOperand(self._path)),
            operation=OPERATIONS["exists"],  # Dummy operation for function result
        )

    def min(self) -> LazyOperation:
        """Get minimum value from collection."""
        return LazyOperation(
            left=FunctionOperand("min", PathOperand(self._path)),
            operation=OPERATIONS["exists"],  # Dummy operation for function result
        )

    def sum(self) -> LazyOperation:
        """Get sum of collection."""
        return LazyOperation(
            left=FunctionOperand("sum", PathOperand(self._path)),
            operation=OPERATIONS["exists"],  # Dummy operation for function result
        )

    def sorted(self, reverse: bool = False) -> LazyOperation:
        """Get sorted collection."""
        return LazyOperation(
            left=FunctionOperand("sorted", PathOperand(self._path), reverse),
            operation=OPERATIONS["exists"],  # Dummy operation for function result
        )

    # =========================================================================
    # VALUE EXTRACTION
    # =========================================================================

    def value(self) -> ValueQuery:
        """
        Get the actual value at this path.

        Returns:
            ValueQuery that resolves to the path value
        """
        return ValueQuery(PathOperand(self._path))

    def evaluate(self, tree: Tree, ctx: Any = None) -> QueryResult:
        """
        Evaluate as a value query (convenience method).

        Args:
            tree: Tree instance
            ctx: Optional context

        Returns:
            Value at this path
        """
        return self.value().evaluate(tree, ctx)

    # =========================================================================
    # LOGICAL OPERATIONS FOR LAZYOPERATION RESULTS
    # =========================================================================

    # Note: These are intentionally not implemented on LazyQuery itself
    # because logical operations should work on LazyOperation instances
    # (the results of comparisons). This maintains clear semantics.

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def __repr__(self) -> str:
        """String representation for debugging."""
        if not self._path:
            return "LazyQuery(root)"
        path_str = ".".join(self._path)
        return f"LazyQuery({path_str})"

    def __bool__(self) -> bool:
        """
        Prevent accidental boolean evaluation.

        Raises:
            TypeError: Always, to prevent misuse
        """
        raise TypeError(
            "LazyQuery objects cannot be used in boolean context. "
            "Use .evaluate(tree) to get the value, or comparison operators "
            "like > or == to create boolean queries."
        )

    @property
    def path(self) -> PathList:
        """
        Get current path as a list.

        Returns:
            Copy of current path
        """
        return self._path.copy()
