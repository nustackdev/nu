"""
Exception classes for the evaluator package.

This module defines the exception hierarchy for evaluator-related errors,
providing specific error types for different failure scenarios.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .expression import Expression

__all__ = [
    "EvaluatorError",
    "EvaluationError",
    "ExpressionError",
    "ContextError",
    "FleetError",
    "ExecutionTimeoutError",
]


class EvaluatorError(Exception):
    """
    Base exception for evaluator errors.

    This is the root exception class for all evaluator-related errors.
    All other evaluator exceptions should inherit from this class.
    """

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        """
        Initialize the evaluator error.

        Args:
            message: Human-readable error message
            cause: Optional underlying exception that caused this error
        """
        super().__init__(message)
        self.cause = cause

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.cause:
            return f"{super().__str__()} (caused by: {self.cause})"
        return super().__str__()


class EvaluationError(EvaluatorError):
    """
    Exception raised when expression evaluation fails.

    This exception is raised when an expression cannot be evaluated
    due to runtime errors, invalid state, or other evaluation issues.
    """

    def __init__(
        self,
        message: str,
        *,
        expression: "Expression | None" = None,
        cause: Exception | None = None,
    ) -> None:
        """
        Initialize the evaluation error.

        Args:
            message: Human-readable error message
            expression: The expression that failed to evaluate
            cause: Optional underlying exception that caused this error
        """
        super().__init__(message, cause=cause)
        self.expression = expression


class ExpressionError(EvaluatorError):
    """
    Exception raised for expression-specific errors.

    This exception is raised when there are issues with expression
    configuration, structure, or validation.
    """

    def __init__(
        self,
        message: str,
        *,
        expression: "Expression | None" = None,
        cause: Exception | None = None,
    ) -> None:
        """
        Initialize the expression error.

        Args:
            message: Human-readable error message
            expression: The expression that has the error
            cause: Optional underlying exception that caused this error
        """
        super().__init__(message, cause=cause)
        self.expression = expression


class ContextError(EvaluatorError):
    """
    Exception raised for context-related errors.

    This exception is raised when there are issues with the execution
    context, such as missing attributes or invalid context state.
    """

    pass


class FleetError(EvaluatorError):
    """
    Exception raised for fleet coordination errors.

    This exception is raised when there are issues with fleet
    coordination, resource management, or distributed execution.
    """

    pass


class ExecutionTimeoutError(EvaluatorError):
    """
    Exception raised when expression execution times out.

    This exception is raised when an expression takes longer than
    the configured timeout to complete execution.
    """

    def __init__(self, message: str, *, timeout: float, cause: Exception | None = None) -> None:
        """
        Initialize the execution timeout error.

        Args:
            message: Human-readable error message
            timeout: The timeout value that was exceeded
            cause: Optional underlying exception that caused this error
        """
        super().__init__(message, cause=cause)
        self.timeout = timeout
