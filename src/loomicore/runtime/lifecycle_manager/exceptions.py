"""
Lifecycle Manager exceptions for error handling.

This module defines specific exceptions for lifecycle management operations
that provide detailed context about what went wrong during resource lifecycle
operations.
"""

from __future__ import annotations

from loomicore.exceptions import ResourceError

__all__ = [
    "LifecycleError",
    "InitializationError",
    "ShutdownError",
    "StateTransitionError",
]


class LifecycleError(ResourceError):
    """
    Base exception for lifecycle management errors.

    This exception indicates failures during lifecycle operations that are
    not covered by more specific error types. It serves as the base for
    lifecycle-specific exceptions.
    """

    pass


class InitializationError(LifecycleError):
    """
    Exception raised when resource initialization fails.

    This exception indicates that a resource could not be initialized due to
    various reasons, such as:
    - Invalid configuration
    - Resource allocation failures
    - Dependency resolution failures

    Example:
        Attempting to initialize a resource with invalid parameters would raise
        this exception.
    """

    pass


class ShutdownError(LifecycleError):
    """
    Exception raised when resource shutdown fails.

    This exception indicates that a resource could not be shut down properly,
    which can occur due to:
    - Resource still being in use
    - Errors during cleanup operations
    - Dependency issues

    Example:
        Attempting to shut down a resource that is still processing requests
        would raise this exception.
    """

    pass


class StateTransitionError(LifecycleError):
    """
    Exception raised when an invalid state transition is attempted.

    This exception indicates that a resource is in a state that does not
    allow the requested operation. For example, trying to initialize an
    already initialized resource or shut down a resource that is not
    initialized.

    Example:
        Attempting to initialize a resource that is already in INITIALIZED state
        would raise this exception.
    """

    pass
