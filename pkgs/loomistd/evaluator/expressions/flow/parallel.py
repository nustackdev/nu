"""
Parallel expression.

This module provides the Parallel expression, which executes multiple expressions
concurrently with configurable concurrency limits.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loomi.evaluator.interface.operations import ParallelOperationProtocol
from loomi.evaluator.interface.types import ErrorBehavior
from loomi.state.interface.type_vars import StateT

from ..base import Expression

if TYPE_CHECKING:
    from ...context import Context


class Parallel(Expression[StateT]):
    """
    Executes expressions concurrently.

    This expression runs child expressions in parallel, with configurable
    maximum concurrency. When max_concurrency is 1, it behaves like
    a Sequence. When negative, it runs all expressions with no limit.

    Args:
        expr: The first expression to execute
        *exprs: Additional expressions to execute in parallel
        max_concurrency: Maximum number of concurrent expressions
            - 1 means sequential execution (same as Sequence)
            - >1 means limit to N concurrent expressions
            - -1 or 0 means unlimited concurrency
        error_behavior: How to handle errors that occur during execution
        on_fail: Expression to execute when an error occurs

    Examples:
        >>> expr1 = Function(func1)
        >>> expr2 = Function(func2)
        >>> expr3 = Function(func3)
        >>> parallel = Parallel(expr1, expr2, expr3, max_concurrency=2)
    """

    def __init__(
        self,
        expr: Expression[StateT],
        /,
        *exprs: Expression[StateT],
        max_concurrency: int = -1,
        error_behavior: ErrorBehavior = "fail",
        on_fail: Expression[StateT] | None = None,
    ):
        """
        Initialize the Parallel expression.

        Args:
            expr: The first expression to execute
            *exprs: Additional expressions to execute in parallel
            max_concurrency: Maximum number of concurrent expressions
                - 1 means sequential execution (same as Sequence)
                - >1 means limit to N concurrent expressions
                - -1 or 0 means unlimited concurrency
            error_behavior: How to handle errors that occur during execution
            on_fail: Expression to execute when an error occurs

        Raises:
            ValueError: If max_concurrency is invalid
        """
        super().__init__(error_behavior=error_behavior, on_fail=on_fail)

        # Validate max_concurrency
        if max_concurrency < -1:
            raise ValueError(f"Invalid max_concurrency: {max_concurrency}. Must be >= -1")

        self._max_concurrency = max_concurrency
        self.children = (expr,) + exprs

    @property
    def max_concurrency(self) -> int:
        """
        Get the maximum number of concurrent expressions.

        Returns:
            The maximum number of concurrent expressions
        """
        return self._max_concurrency


if TYPE_CHECKING:
    _: type[ParallelOperationProtocol[Expression, "Context"]] = Parallel
