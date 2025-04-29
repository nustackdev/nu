"""
Exceptions for the app module.

This module provides custom exceptions for the app module, including
- AppError: Base class for all app-related exceptions
- DependencyError: Raised for dependency-related errors
- ServiceDependencyError: Raised for service-related errors
- StateError: Raised for state-related errors
- ExecutionError: Raised for execution-related errors
"""

from __future__ import annotations

from typing import Any, Type

__all__ = [
    "AppError",
    "DependencyError",
    "ServiceDependencyError",
    "StateError",
]


class AppError(Exception):
    """Base class all app-related exceptions."""

    pass


class DependencyError(AppError):
    """
    Raised for dependency-related errors.

    Examples:
    - Missing dependency
    - Circular dependency
    - Initialization failure
    """

    def __init__(self, message: str, dependency_type: Type | None = None, **context: Any) -> None:
        self.dependency_type = dependency_type
        self.context = context
        super().__init__(message)


class ServiceDependencyError(AppError):
    """
    Raised for service-related errors.

    Examples:
    - Serivce dependency errors
    - Service lifecycle errors
    """

    pass


class StateError(AppError):
    """
    Raised for state-related errors.

    Examples:
    - Invalid state access
    - State modification failure
    - State adapter errors
    """

    def __init__(self, message: str, key: tuple[str, ...] | None = None, **context: Any) -> None:
        self.key = key
        self.context = context
        super().__init__(message)


class ExecutionError(AppError):
    """
    Raised for execution-related errors.

    Examples:
    - Execution failure
    - Invalid execution type
    - Platform errors
    """

    pass
