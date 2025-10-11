"""Exception hierarchy for the query system.

This module defines query-specific exceptions that provide clear
error handling and debugging information for query operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .query import Query

__all__ = [
    "QueryError",
    "QueryEvaluationError",
    "QueryOperationError",
    "QuerySyntaxError",
]


class QueryError(Exception):
    """Base exception class for all query-related errors."""

    def __init__(self, message: str, query: Query | None = None) -> None:
        super().__init__(message)
        self.query = query


class QueryEvaluationError(QueryError):
    """Raised when query evaluation fails against tree data."""

    def __init__(
        self, message: str, query: Query | None = None, original_error: Exception | None = None
    ) -> None:
        super().__init__(message, query)
        self.original_error = original_error


class QueryOperationError(QueryError):
    """Raised when a query operation fails during execution."""

    def __init__(
        self,
        message: str,
        operation: str | None = None,
        operands: tuple | None = None,
        original_error: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.operation = operation
        self.operands = operands
        self.original_error = original_error


class QuerySyntaxError(QueryError):
    """Raised when query syntax or structure is invalid."""

    def __init__(self, message: str, query: Query | None = None, details: str | None = None) -> None:
        super().__init__(message, query)
        self.details = details
