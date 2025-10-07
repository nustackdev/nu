"""
Exception hierarchy for the path module.

This module defines path-specific exceptions that provide clear
error handling and debugging information for path operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .path import Path

__all__ = [
    "PathError",
    "PathConstructionError",
    "PathEvaluationError",
    "PathNotFoundError",
]


class PathError(Exception):
    """Base exception class for all path-related errors."""

    def __init__(self, message: str, path: Path | None = None):
        super().__init__(message)
        self.path = path


class PathConstructionError(PathError):
    """Raised when path construction fails due to invalid components or operations."""

    def __init__(self, message: str, path: Path | None = None, component: str | None = None):
        super().__init__(message, path)
        self.component = component


class PathEvaluationError(PathError):
    """Raised when path evaluation fails against tree data."""

    def __init__(
        self, message: str, path: Path | None = None, original_error: Exception | None = None
    ):
        super().__init__(message, path)
        self.original_error = original_error


class PathNotFoundError(PathEvaluationError):
    """Raised when a path does not exist in the tree during evaluation."""

    def __init__(self, message: str, path: Path | None = None, component: str | None = None):
        super().__init__(message, path)
        self.component = component
