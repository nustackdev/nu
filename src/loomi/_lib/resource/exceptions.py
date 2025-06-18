"""
Resource-related exceptions for error handling.

This module defines the hierarchy of exceptions that can be raised during
resource lifecycle operations. It provides specific exception types for different
failure scenarios:

- CreationError: For resource instantiation failures
- StateError: For invalid state transitions or operations
- SpecError: For specification-related issues

The exceptions form a hierarchy with ResourceError as the base for resource-specific
errors, allowing for both specific and general error catching as needed.

Example:
    try:
        resource = MyResource(spec)
    except CreationError as e:
        # Handle creation-specific error
        logger.error(f"Failed to create resource: {e}")
    except ResourceError as e:
        # Handle any resource-related error
        logger.error(f"Resource error occurred: {e}")
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "CreationError",
    "StateError",
    "SpecError",
]


class ResourceError(Exception):
    """
    Base class for resource-related exceptions.

    This exception serves as the base for all resource-related errors,
    allowing for specific error types to inherit from it. It provides
    a common interface for handling resource errors in a consistent manner.
    """

    pass


class CreationError(ResourceError):
    """
    Exception raised when resource creation fails.

    This exception indicates failures during resource instantiation, which
    can include:
    - Invalid constructor arguments
    - Resource allocation failures
    - Dependency resolution failures
    - Initialization errors

    Note:
        This exception does not inherit from ResourceError since it may occur
        before the resource is fully constructed.
    """

    pass


class StateError(ResourceError):
    """
    Exception raised when a resource is in an invalid state for an operation.

    This exception indicates state-related failures such as:
    - Attempting operations before initialization
    - Operating on a shutdown resource
    - Invalid state transitions
    - Concurrent state modification issues

    The exception inherits from ResourceError to allow catching all
    resource-related errors when needed.
    """

    pass


class SpecError(ResourceError):
    """
    Exception raised for resource specification errors.

    This exception indicates specification-related failures such as:
    - Invalid specification format
    - Missing required specification fields
    - Incompatible specification values
    - Factory configuration errors

    The exception inherits from ResourceError to allow catching all
    resource-related errors when needed.
    """

    pass


class InitializationError(ResourceError):
    """Raised when resource initialization fails."""

    pass


class ShutdownError(ResourceError):
    """Raised when resource shutdown fails."""

    pass


class DependencyError(ResourceError):
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
