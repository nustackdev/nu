"""
Error types and utilities for the operations framework.

This module defines the error hierarchy and helper functions for
consistent error handling throughout the operations framework.
"""

import traceback
from typing import Any, Dict, Optional, Tuple


class OperationError(Exception):
    """
    Base class for all operation-related errors.

    Provides context about where the error occurred and what the operation
    was attempting to do.
    """

    def __init__(
        self,
        message: str,
        operation=None,
        context=None,
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

        if self.context and hasattr(self.context, "path"):
            parts.append(f"Context path: {self.context.path}")

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

    This error is raised by the Timeout operation when the wrapped
    operation takes longer than the specified timeout.
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


def wrap_error(error: Exception, operation=None, context=None) -> OperationError:
    """
    Wrap a generic exception in an appropriate OperationError.

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
