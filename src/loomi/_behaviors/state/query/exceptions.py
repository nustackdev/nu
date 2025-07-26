"""
Exception hierarchy for the query system.

This module defines query-specific exceptions that provide clear
error handling and debugging information.
"""

from __future__ import annotations

__all__ = [
    "QueryError",
    "QuerySyntaxError",
    "QueryEvaluationError",
    "PathNotFoundError",
    "OperationNotSupportedError",
    "OperandResolutionError",
    "InvalidOperationError",
    "CacheError",
]


class QueryError(Exception):
    """Base exception class for all query-related errors."""

    def __init__(self, message: str, query: str = None, path: list[str] = None):
        super().__init__(message)
        self.query = query
        self.path = path


class QuerySyntaxError(QueryError):
    """Raised when query syntax is invalid."""

    pass


class QueryEvaluationError(QueryError):
    """Raised when error occurs during query evaluation."""

    def __init__(
        self,
        message: str,
        query: str = None,
        path: list[str] = None,
        original_error: Exception = None,
    ):
        super().__init__(message, query, path)
        self.original_error = original_error


class PathNotFoundError(QueryError):
    """Raised when a query path does not exist in the tree."""

    def __init__(self, path: list[str], message: str = None):
        if message is None:
            path_str = ".".join(path) if path else "root"
            message = f"Path not found: {path_str}"
        super().__init__(message, path=path)


class OperationNotSupportedError(QueryError):
    """Raised when an operation is not supported on the given operand types."""

    def __init__(self, operation: str, left_type: type, right_type: type = None):
        if right_type is None:
            message = f"Unary operation '{operation}' not supported on type {left_type.__name__}"
        else:
            message = f"Binary operation '{operation}' not supported on types {left_type.__name__} and {right_type.__name__}"
        super().__init__(message)
        self.operation = operation
        self.left_type = left_type
        self.right_type = right_type


class OperandResolutionError(QueryError):
    """Raised when an operand cannot be resolved to a value."""

    def __init__(self, operand_type: str, message: str = None, original_error: Exception = None):
        if message is None:
            message = f"Failed to resolve {operand_type} operand"
        super().__init__(message)
        self.operand_type = operand_type
        self.original_error = original_error


class InvalidOperationError(QueryError):
    """Raised when operation configuration is invalid."""

    def __init__(self, operation: str, reason: str):
        message = f"Invalid operation '{operation}': {reason}"
        super().__init__(message)
        self.operation = operation
        self.reason = reason


class CacheError(QueryError):
    """Raised when cache operations fail."""

    pass
