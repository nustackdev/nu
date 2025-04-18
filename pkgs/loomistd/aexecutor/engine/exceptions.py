"""
Custom exceptions for the operations execution engine.

This module defines the exception hierarchy for the execution engine,
providing rich context information and consistent error handling.
"""

from __future__ import annotations

import traceback
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple, TypeVar

if TYPE_CHECKING:
    pass

    from ..context.context import Context
    from ..operations.base import Operation

# Type variable for operation type
OperationT = TypeVar("OperationT")
ContextT = TypeVar("ContextT")


class OperationError(Exception):
    """
    Base class for all operation-related errors.

    Provides context about where the error occurred and what the operation
    was attempting to do.

    Attributes:
        operation: The operation that raised the error
        context: The execution context when the error occurred
        state_path: The state path involved in the error
        config: Additional configuration that led to the error
        cause: The original exception that caused this error
        traceback: The formatted traceback when the error occurred
    """

    def __init__(
        self,
        message: str,
        operation: Optional[Operation] = None,
        context: Optional[Context] = None,
        state_path: Optional[Tuple[str, ...]] = None,
        config: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        self.operation = operation
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

        if self.operation:
            op_name = getattr(self.operation, "__class__", self.operation).__name__
            parts.append(f"Operation: {op_name}")

        if self.context and hasattr(self.context, "scope") and hasattr(self.context.scope, "path"):
            parts.append(f"Context path: {self.context.scope.path}")

        if self.state_path:
            parts.append(f"State path: {self.state_path}")

        if self.config:
            config_str = ", ".join(f"{k}={v}" for k, v in self.config.items())
            parts.append(f"Config: {config_str}")

        if self.cause:
            parts.append(f"Caused by: {type(self.cause).__name__}: {self.cause}")

        return " | ".join(parts)


class OperationTimeoutError(OperationError):
    """
    Raised when an operation exceeds its time limit.

    This error is raised when an operation takes longer than the specified timeout.
    """

    pass


class OperationCancelledError(OperationError):
    """
    Raised when an operation is explicitly cancelled.

    This error is raised when an operation is cancelled through
    the cancellation mechanism provided by the execution engine.
    """

    pass


class StateAccessError(OperationError):
    """
    Raised when there's an error accessing state.

    This error is raised when an operation fails to access state
    at a specified path, either due to the path not existing or
    due to a type mismatch.
    """

    pass


class OperationConfigError(OperationError):
    """
    Raised when there's an error in operation configuration.

    This error is raised when an operation is configured incorrectly,
    such as providing incompatible parameters or missing required parameters.
    """

    pass


class OperationExecutionError(OperationError):
    """
    Raised when an operation fails during execution.

    This error is raised when an operation encounters an error during
    execution that is not covered by more specific error types.
    """

    pass


def wrap_error(
    error: Exception, operation: Optional[Operation] = None, context: Optional[Context] = None
) -> OperationError:
    """
    Wrap a generic exception in an appropriate OperationError.

    This function examines the type of the original exception and wraps it
    in the most specific OperationError subclass that applies. If the original
    exception is already an OperationError, it is returned unchanged.

    Args:
        error: The original exception
        operation: The operation that raised the exception
        context: The execution context when the exception was raised

    Returns:
        An OperationError instance wrapping the original exception
    """
    if isinstance(error, OperationError):
        return error

    return OperationExecutionError(
        str(error),
        operation=operation,
        context=context,
        cause=error,
    )
