"""
Error handling for the operations framework.

This module defines the error hierarchy and utilities for error handling
in the Loomi operations framework.
"""

from __future__ import annotations

import traceback
from typing import Any, Dict, Optional

from .operation import StatePath

__all__ = [
    "OperationError",
    "OperationTimeoutError",
    "OperationCancelledError",
    "StateAccessError",
    "OperationConfigError",
    "OperationNotFoundError",
    "enrich_error",
]


class OperationError(Exception):
    """Base class for all operation-related errors.

    This is the parent class for all errors that can occur during
    operation execution.

    Attributes:
        message: The error message
        operation_id: ID of the operation where the error occurred
        operation_type: Type of operation where the error occurred
        details: Additional error details as a dictionary
        cause: Original exception that caused this error
    """

    def __init__(
        self,
        message: str,
        operation_id: Optional[str] = None,
        operation_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        """Initialize the error with context information.

        Args:
            message: Error message
            operation_id: ID of the operation where the error occurred
            operation_type: Type of operation where the error occurred
            details: Additional error details
            cause: Original exception that caused this error
        """
        self.operation_id = operation_id
        self.operation_type = operation_type
        self.details = details or {}
        self.cause = cause

        # Build the full error message
        full_message = message
        if operation_type:
            full_message = f"{operation_type}: {full_message}"
        if operation_id:
            full_message = f"{full_message} (op_id: {operation_id})"

        super().__init__(full_message)


class OperationTimeoutError(OperationError):
    """Error raised when an operation exceeds its time limit.

    Attributes:
        timeout: The timeout duration in seconds
    """

    def __init__(
        self,
        timeout: float,
        operation_id: Optional[str] = None,
        operation_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the timeout error.

        Args:
            timeout: Timeout duration in seconds
            operation_id: ID of the operation that timed out
            operation_type: Type of operation that timed out
            details: Additional error details
        """
        message = f"Operation timed out after {timeout} seconds"
        super().__init__(
            message=message,
            operation_id=operation_id,
            operation_type=operation_type,
            details=details,
        )
        self.timeout = timeout


class OperationCancelledError(OperationError):
    """Error raised when an operation is cancelled.

    This error is raised when an operation is explicitly cancelled,
    either through a cancellation token or by cancelling the task.
    """

    def __init__(
        self,
        operation_id: Optional[str] = None,
        operation_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the cancellation error.

        Args:
            operation_id: ID of the operation that was cancelled
            operation_type: Type of operation that was cancelled
            details: Additional error details
        """
        message = "Operation was cancelled"
        super().__init__(
            message=message,
            operation_id=operation_id,
            operation_type=operation_type,
            details=details,
        )


class StateAccessError(OperationError):
    """Error raised when there's an issue accessing state.

    This error occurs when an operation attempts to access state
    but encounters a problem, such as a missing path or type mismatch.

    Attributes:
        state_path: The path to the state being accessed
    """

    def __init__(
        self,
        message: str,
        state_path: Optional[StatePath] = None,
        operation_id: Optional[str] = None,
        operation_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        """Initialize the state access error.

        Args:
            message: Error message
            state_path: Path to the state being accessed
            operation_id: ID of the operation where the error occurred
            operation_type: Type of operation where the error occurred
            details: Additional error details
            cause: Original exception that caused this error
        """
        if state_path:
            message = f"{message} (path: {'.'.join(str(p) for p in state_path)})"
            details = details or {}
            details["state_path"] = state_path

        super().__init__(
            message=message,
            operation_id=operation_id,
            operation_type=operation_type,
            details=details,
            cause=cause,
        )
        self.state_path = state_path


class OperationConfigError(OperationError):
    """Error raised when an operation is configured incorrectly.

    This error occurs when an operation receives invalid configuration,
    such as missing required parameters or incompatible values.

    Attributes:
        parameter: The name of the parameter with the issue
    """

    def __init__(
        self,
        message: str,
        parameter: Optional[str] = None,
        operation_id: Optional[str] = None,
        operation_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the configuration error.

        Args:
            message: Error message
            parameter: Name of the parameter with the issue
            operation_id: ID of the operation where the error occurred
            operation_type: Type of operation where the error occurred
            details: Additional error details
        """
        if parameter:
            message = f"Invalid configuration for parameter '{parameter}': {message}"
            details = details or {}
            details["parameter"] = parameter

        super().__init__(
            message=message,
            operation_id=operation_id,
            operation_type=operation_type,
            details=details,
        )
        self.parameter = parameter


class OperationNotFoundError(OperationError):
    """Error raised when an operation cannot be found.

    This error occurs when attempting to find an operation that doesn't exist,
    such as when looking up by ID or when a required child operation is missing.
    """

    def __init__(
        self,
        message: str,
        operation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the not found error.

        Args:
            message: Error message
            operation_id: ID of the operation that couldn't be found
            details: Additional error details
        """
        super().__init__(
            message=message,
            operation_id=operation_id,
            details=details,
        )


def enrich_error(
    error: Exception,
    operation_id: Optional[str] = None,
    operation_type: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> OperationError:
    """Enrich an exception with operation context.

    This utility function enriches an exception with operation context,
    either by updating an existing OperationError or by wrapping
    another exception type.

    Args:
        error: The original exception
        operation_id: ID of the operation where the error occurred
        operation_type: Type of operation where the error occurred
        details: Additional error details

    Returns:
        An OperationError with context information
    """
    if isinstance(error, OperationError):
        # If it's already an OperationError, update it with any missing context
        if operation_id and not error.operation_id:
            error.operation_id = operation_id
        if operation_type and not error.operation_type:
            error.operation_type = operation_type
        if details:
            error.details.update(details)
        return error

    # Get the exception traceback as a string
    tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))

    # Create details with the traceback
    enriched_details = {"traceback": tb}
    if details:
        enriched_details.update(details)

    # Wrap other exception types in an OperationError
    return OperationError(
        message=str(error),
        operation_id=operation_id,
        operation_type=operation_type,
        details=enriched_details,
        cause=error,
    )
