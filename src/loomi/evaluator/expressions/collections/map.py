"""
Map expression.

This module provides the Map expression, which executes an expression
for each item in a collection from the state.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple, Union

from loomi.evaluator.interface.types import ErrorBehavior

from ..base import Expression
from ..metadata import ExpressionMetadata

if TYPE_CHECKING:
    pass


class Map(Expression):
    """
    Executes an expression for each item in a collection.

    This expression retrieves a dictionary from the state using the specified
    path, then executes the provided expression once for each item. Expressions can be
    executed sequentially or concurrently based on max_concurrency.

    The context for each executed expression is enriched with 'map_key' (the key or index
    of the current item) and 'map_index' (the position in the iteration).

    Args:
        expr: The expression to execute for each item
        items_path: Path to the collection in state
        max_concurrency: Maximum number of concurrent expressions
            - 1 means sequential execution
            - >1 means limited concurrent execution
            - 0 or -1 means unlimited concurrency
        error_behavior: How to handle errors that occur during execution
        on_fail: Expression to execute when an error occurs

    Examples:
        >>> # Process items sequentially
        >>> map_expr = Map(
        ...     Function(process_item),
        ...     items_path=("data", "items"),
        ... )
        >>>
        >>> # Process items concurrently (up to 5 at a time)
        >>> map_expr = Map(
        ...     Function(process_item),
        ...     items_path=("data", "items"),
        ...     max_concurrency=5,
        ... )
    """

    def __init__(
        self,
        expr: Expression,
        /,
        *,
        items_path: Union[Tuple[str, ...], str],
        max_concurrency: int = 1,
        error_behavior: ErrorBehavior = "fail",
        on_fail: Optional[Expression] = None,
    ):
        """
        Initialize the Map expression.

        Args:
            expr: The expression to execute for each item
            items_path: Path to the collection in state
            max_concurrency: Maximum number of concurrent expressions
                - 1 means sequential execution
                - >1 means limited concurrent execution
                - 0 or -1 means unlimited concurrency
            error_behavior: How to handle errors that occur during execution
            on_fail: Expression to execute when an error occurs

        Raises:
            ValueError: If items_path is empty or max_concurrency is invalid
        """
        super().__init__(error_behavior=error_behavior, on_fail=on_fail)

        if not items_path:
            raise ValueError("items_path must be provided")

        if max_concurrency < -1:
            raise ValueError(f"Invalid max_concurrency: {max_concurrency}. Must be >= -1")

        self._expr = expr

        # Normalize items_path to tuple
        if isinstance(items_path, str):
            self._items_path = (items_path,)
        else:
            self._items_path = items_path

        self._max_concurrency = max_concurrency

        # Set child expression
        self.children = (expr,)

    @property
    def map_expr(self) -> Expression:
        """
        Get the expression to execute for each item.

        Returns:
            The expression to execute
        """
        return self._expr

    @property
    def items_path(self) -> Tuple[str, ...]:
        """
        Get the path to the collection in state.

        Returns:
            The path to the collection
        """
        return self._items_path

    @property
    def max_concurrency(self) -> int:
        """
        Get the maximum number of concurrent expressions.

        Returns:
            The maximum number of concurrent expressions
        """
        return self._max_concurrency

    @property
    def metadata(self) -> ExpressionMetadata:
        """
        Get the expression's metadata.

        Returns:
            The expression metadata
        """
        metadata = super().metadata

        custom_properties = {
            "items_path": self._items_path,
            "max_concurrency": self._max_concurrency,
        }

        return metadata.with_properties(**custom_properties)
