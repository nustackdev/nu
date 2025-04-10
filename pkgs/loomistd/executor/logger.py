"""
Logging utilities for the operations framework.

This module provides a consistent logging interface for the operations framework.
"""

import logging
from typing import Any, Dict, Optional

# Set up logger
logger = logging.getLogger("loomi.executor")


def format_operation_log(
    operation_name: str,
    context_path: str,
    status: str = "info",
    details: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Format a log message for an operation.

    Creates a consistent log message format for operations, including
    the operation name, context path, status, and any additional details.

    Args:
        operation_name: Name of the operation
        context_path: Path of the execution context
        status: Status of the operation (start, end, error, etc.)
        details: Additional details to include in the log

    Returns:
        Formatted log message
    """
    msg_parts = [f"Operation[{operation_name}]"]

    if context_path:
        path_str = ".".join(str(p) for p in context_path)
        msg_parts.append(f"Path[{path_str}]")

    msg_parts.append(f"Status[{status}]")

    if details:
        details_str = " ".join(f"{k}={v}" for k, v in details.items())
        msg_parts.append(f"Details[{details_str}]")

    return " ".join(msg_parts)


def log_operation_start(operation_name: str, context_path: str, **kwargs) -> None:
    """
    Log the start of an operation.

    Args:
        operation_name: Name of the operation
        context_path: Path of the execution context
        **kwargs: Additional details to include in the log
    """
    logger.debug(
        format_operation_log(
            operation_name,
            context_path,
            status="start",
            details=kwargs if kwargs else None,
        )
    )


def log_operation_end(operation_name: str, context_path: str, **kwargs) -> None:
    """
    Log the end of an operation.

    Args:
        operation_name: Name of the operation
        context_path: Path of the execution context
        **kwargs: Additional details to include in the log
    """
    logger.debug(
        format_operation_log(
            operation_name,
            context_path,
            status="end",
            details=kwargs if kwargs else None,
        )
    )


def log_operation_error(
    operation_name: str,
    error: BaseException,
    context_path: str,
    **kwargs,
) -> None:
    """
    Log an error in an operation.

    Args:
        operation_name: Name of the operation
        error: The error that occurred
        context_path: Path of the execution context
        **kwargs: Additional details to include in the log
    """
    logger.error(
        format_operation_log(
            operation_name,
            context_path,
            status="error",
            details=(
                {"error_type": type(error).__name__, "error": str(error), **kwargs}
                if kwargs
                else {"error_type": type(error).__name__, "error": str(error)}
            ),
        )
    )
