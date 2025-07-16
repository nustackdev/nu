"""
Custom exceptions for the expressions execution engine.

This module defines the exception hierarchy for the execution engine,
providing rich context information and consistent error handling.
"""

from __future__ import annotations

import traceback
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple, TypeVar

if TYPE_CHECKING:
    pass

    from ..context import Context
    from ..expressions import Expression

# Type variable for expression type
ExpressionT = TypeVar("ExpressionT")
ContextT = TypeVar("ContextT")


class ExpressionError(Exception):
    """
    Base class for all expression-related errors.

    Provides context about where the error occurred and what the expression
    was attempting to do.

    Attributes:
        expression: The expression that raised the error
        context: The execution context when the error occurred
        state_path: The state path involved in the error
        config: Additional configuration that led to the error
        cause: The original exception that caused this error
        traceback: The formatted traceback when the error occurred
    """

    def __init__(
        self,
        message: str,
        expression: Optional[Expression] = None,
        context: Optional[Context] = None,
        state_path: Optional[Tuple[str, ...]] = None,
        config: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        self.expression = expression
        self.context = context
        self.state_path = state_path
        self.config = config or {}
        self.cause = cause

        # Capture stack trace
        self.traceback = traceback.format_exc()

        super().__init__(message)

    def __str__(self) -> str:
        """Format error message with context information."""
        parts = [super().__str__()]

        if self.expression:
            op_name = getattr(self.expression, "__class__", self.expression).__name__
            parts.append(f"Expression: {op_name}")

        if self.state_path:
            parts.append(f"State path: {self.state_path}")

        if self.config:
            config_str = ", ".join(f"{k}={v}" for k, v in self.config.items())
            parts.append(f"Config: {config_str}")

        if self.cause:
            parts.append(f"Caused by: {type(self.cause).__name__}: {self.cause}")

        return " | ".join(parts)


class ExpressionTimeoutError(ExpressionError):
    """
    Raised when an expression exceeds its time limit.

    This error is raised when an expression takes longer than the specified timeout.
    """

    pass


class ExpressionCancelledError(ExpressionError):
    """
    Raised when an expression is explicitly cancelled.

    This error is raised when an expression is cancelled through
    the cancellation mechanism provided by the execution engine.
    """

    pass


class StateAccessError(ExpressionError):
    """
    Raised when there's an error accessing state.

    This error is raised when an expression fails to access state
    at a specified path, either due to the path not existing or
    due to a type mismatch.
    """

    pass


class ExpressionConfigError(ExpressionError):
    """
    Raised when there's an error in expression configuration.

    This error is raised when an expression is configured incorrectly,
    such as providing incompatible parameters or missing required parameters.
    """

    pass


class ExpressionExecutionError(ExpressionError):
    """
    Raised when an expression fails during execution.

    This error is raised when an expression encounters an error during
    execution that is not covered by more specific error types.
    """

    pass


def wrap_error(
    error: Exception, expression: Optional[Expression] = None, context: Optional[Context] = None
) -> ExpressionError:
    """
    Wrap a generic exception in an appropriate ExpressionError.

    This function examines the type of the original exception and wraps it
    in the most specific ExpressionError subclass that applies. If the original
    exception is already an ExpressionError, it is returned unchanged.

    Args:
        error: The original exception
        expression: The expression that raised the exception
        context: The execution context when the exception was raised

    Returns:
        An ExpressionError instance wrapping the original exception
    """
    if isinstance(error, ExpressionError):
        return error

    return ExpressionExecutionError(
        str(error),
        expression=expression,
        context=context,
        cause=error,
    )
