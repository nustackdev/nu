"""
Timeout expression.

This module provides the Timeout expression, which adds a timeout
constraint to an expression's execution.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from loomi.evaluator.interface.operations import TimeoutOperationProtocol
from loomi.evaluator.interface.types import ErrorBehavior
from loomi.state.interface.type_vars import StateT

from ..base import Expression

if TYPE_CHECKING:
    from ...context import Context


class Timeout(Expression[StateT]):
    """
    Adds a timeout constraint to an expression.

    This expression executes a child expression with a timeout constraint,
    cancelling it if execution exceeds the specified timeout duration.
    Optionally executes an on_timeout expression if the timeout is reached.

    Args:
        expr: The expression to execute with a timeout
        timeout: Timeout duration in seconds
        on_timeout: Expression to execute if the timeout is reached
        error_behavior: How to handle errors that occur during execution
        on_fail: Expression to execute when an error occurs

    Examples:
        >>> # Execute with a 5-second timeout
        >>> timeout_op = Timeout(
        ...     Function(long_running_task),
        ...     timeout=5.0,
        ...     on_timeout=Function(handle_timeout)
        ... )
    """

    def __init__(
        self,
        expr: Expression[StateT],
        /,
        *,
        timeout: float = 30.0,
        on_timeout: Optional[Expression[StateT]] = None,
        error_behavior: ErrorBehavior = "fail",
        on_fail: Optional[Expression[StateT]] = None,
    ):
        """
        Initialize the Timeout expression.

        Args:
            expr: The expression to execute with a timeout
            timeout: Timeout duration in seconds
            on_timeout: Expression to execute if the timeout is reached
            error_behavior: How to handle errors that occur during execution
            on_fail: Expression to execute when an error occurs

        Raises:
            ValueError: If timeout is not positive
        """
        super().__init__(error_behavior=error_behavior, on_fail=on_fail)

        if timeout <= 0:
            raise ValueError(f"Timeout must be positive, got {timeout}")

        self._expr = expr
        self._timeout = timeout
        self._on_timeout = on_timeout

        # Set child expressions
        children = [expr]
        if on_timeout:
            children.append(on_timeout)
        self.children = tuple(children)

    @property
    def timeout_expr(self) -> Expression[StateT]:
        """
        Get the expression to execute with a timeout.

        Returns:
            The expression to execute
        """
        return self._expr

    @property
    def timeout(self) -> float:
        """
        Get the timeout duration in seconds.

        Returns:
            The timeout duration
        """
        return self._timeout

    @property
    def on_timeout(self) -> Optional[Expression[StateT]]:
        """
        Get the expression to execute if the timeout is reached.

        Returns:
            The on_timeout expression or None if not specified
        """
        return self._on_timeout


if TYPE_CHECKING:
    _: type[TimeoutOperationProtocol[Expression, "Context"]] = Timeout
