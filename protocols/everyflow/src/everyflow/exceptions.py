"""Exceptions for EveryFlow."""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from everyflow.runtime import Path


__all__ = [
    "CancelledError",
    "ContextError",
    "ExecutionError",
    "FlowError",
    "RetryExhaustedError",
    "TimeoutError",
]


class FlowError(Exception):
    """Base exception for all flow-related errors."""

    def __init__(self, message: str, *, path: Path | None = None) -> None:
        """Initialize exception."""
        super().__init__(message)
        self.path = path

    def __str__(self) -> str:
        base = super().__str__()
        if self.path:
            return f"{base} [path={self.path}]"
        return base


class CancelledError(FlowError):
    """Raised when a flow is cancelled."""

    def __init__(
        self,
        message: str = "Flow was cancelled",
        *,
        path: Path | None = None,
        reason: str | None = None,
    ) -> None:
        """Initialize exception."""
        super().__init__(message, path=path)
        self.reason = reason


class ContextError(FlowError):
    """Raised for context-related errors."""

    pass


class ExecutionError(FlowError):
    """Raised when flow execution fails."""

    def __init__(
        self,
        message: str,
        *,
        path: Path | None = None,
        cause: Exception | None = None,
    ) -> None:
        """Initialize exception."""
        super().__init__(message, path=path)
        self.cause = cause
        self.__cause__ = cause


class TimeoutError(FlowError):
    """Raised when a flow times out."""

    def __init__(
        self,
        message: str = "Flow timed out",
        *,
        path: Path | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        """Initialize exception."""
        super().__init__(message, path=path)
        self.timeout_seconds = timeout_seconds


class RetryExhaustedError(FlowError):
    """Raised when all retry attempts are exhausted."""

    def __init__(
        self,
        message: str = "Retry attempts exhausted",
        *,
        path: Path | None = None,
        attempts: int | None = None,
        last_error: Exception | None = None,
    ) -> None:
        """Initialize exception."""
        super().__init__(message, path=path)
        self.attempts = attempts
        self.last_error = last_error
        if last_error:
            self.__cause__ = last_error
