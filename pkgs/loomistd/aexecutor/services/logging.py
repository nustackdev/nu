"""
Logging utilities for the operations framework.

This module provides a consistent logging interface for the operations framework.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import attrs

from loomi.service import AsyncService
from loomi.spec import Spec

from .logger import logger

__all__ = [
    "LoggingService",
]


class LoggingService(AsyncService):
    @staticmethod
    def format_operation_log(
        operation_name: str,
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
        msg_parts = [f"Operation: '{operation_name}'"]

        msg_parts.append(f"Status: '{status}'")

        if details:
            details_str = " ".join(f"{k}={v}" for k, v in details.items())
            msg_parts.append(f"Details: {details_str}]")

        return ", ".join(msg_parts)

    def log_operation_start(self, operation_name: str, **kwargs) -> None:
        """
        Log the start of an operation.

        Args:
            operation_name: Name of the operation
            context_path: Path of the execution context
            **kwargs: Additional details to include in the log
        """
        logger.debug(
            self.format_operation_log(
                operation_name,
                status="start",
                details=kwargs if kwargs else None,
            )
        )

    def log_operation_end(self, operation_name: str, **kwargs) -> None:
        """
        Log the end of an operation.

        Args:
            operation_name: Name of the operation
            context_path: Path of the execution context
            **kwargs: Additional details to include in the log
        """
        logger.debug(
            self.format_operation_log(
                operation_name,
                status="end",
                details=kwargs if kwargs else None,
            )
        )

    def log_operation_error(
        self,
        operation_name: str,
        error: BaseException,
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
            self.format_operation_log(
                operation_name,
                status="error",
                details=(
                    {"error_type": type(error).__name__, "error": str(error), **kwargs}
                    if kwargs
                    else {"error_type": type(error).__name__, "error": str(error)}
                ),
            )
        )

    def debug(self, message: str) -> None:
        """
        Log a debug message.

        Args:
            message: The debug message to log
        """
        logger.debug(message)

    def info(self, message: str) -> None:
        """
        Log an info message.

        Args:
            message: The info message to log
        """
        logger.info(message)

    def warning(self, message: str) -> None:
        """
        Log a warning message.

        Args:
            message: The warning message to log
        """
        logger.warning(message)

    def error(self, message: str, exc_info: Exception | None = None) -> None:
        """
        Log an error message.
        Args:
            message: The error message to log
        """
        logger.error(message, exc_info=exc_info)

    def critical(self, message: str) -> None:
        """
        Log a critical message.
        Args:
            message: The critical message to log
        """
        logger.critical(message)


@attrs.define(frozen=True, slots=True, kw_only=True)
class LoggingServiceSpec(Spec):
    name: str = "logging_service"
    factory: type = LoggingService
