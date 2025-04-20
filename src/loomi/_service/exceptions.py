"""
Service-related exceptions for error handling.

This module defines the hierarchy of exceptions that can be raised during
service lifecycle operations. It provides specific exception types for different
failure scenarios:

- CreationError: For service instantiation failures
- StateError: For invalid state transitions or operations
- SpecError: For specification-related issues

The exceptions form a hierarchy with ServiceError as the base for service-specific
errors, allowing for both specific and general error catching as needed.

Example:
    try:
        service = MyService(spec)
    except CreationError as e:
        # Handle creation-specific error
        logger.error(f"Failed to create service: {e}")
    except ServiceError as e:
        # Handle any service-related error
        logger.error(f"Service error occurred: {e}")
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "CreationError",
    "StateError",
    "SpecError",
]


class ServiceError(Exception):
    """
    Base class for service-related exceptions.

    This exception serves as the base for all service-related errors,
    allowing for specific error types to inherit from it. It provides
    a common interface for handling service errors in a consistent manner.
    """

    pass


class CreationError(ServiceError):
    """
    Exception raised when service creation fails.

    This exception indicates failures during service instantiation, which
    can include:
    - Invalid constructor arguments
    - Resource allocation failures
    - Dependency resolution failures
    - Initialization errors

    Note:
        This exception does not inherit from ServiceError since it may occur
        before the service is fully constructed.
    """

    pass


class StateError(ServiceError):
    """
    Exception raised when a service is in an invalid state for an operation.

    This exception indicates state-related failures such as:
    - Attempting operations before initialization
    - Operating on a shutdown service
    - Invalid state transitions
    - Concurrent state modification issues

    The exception inherits from ServiceError to allow catching all
    service-related errors when needed.
    """

    pass


class SpecError(ServiceError):
    """
    Exception raised for service specification errors.

    This exception indicates specification-related failures such as:
    - Invalid specification format
    - Missing required specification fields
    - Incompatible specification values
    - Factory configuration errors

    The exception inherits from ServiceError to allow catching all
    service-related errors when needed.
    """

    pass


class InitializationError(ServiceError):
    """Raised when service initialization fails."""

    pass


class ShutdownError(ServiceError):
    """Raised when service shutdown fails."""

    pass


class DependencyError(ServiceError):
    """
    Raised for dependency-related errors.

    Examples:
    - Missing dependency
    - Circular dependency
    - Initialization failure
    """

    def __init__(self, message: str, dependency_type: type | None = None, **context: Any) -> None:
        self.dependency_type = dependency_type
        self.context = context
        super().__init__(message)
