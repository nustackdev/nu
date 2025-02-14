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

from loomi.service.exceptions import ServiceError

__all__ = [
    "CreationError",
    "StateError",
    "SpecError",
]


class CreationError(Exception):
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


__all__ = [
    "CreationError",
    "StateError",
    "SpecError",
]
