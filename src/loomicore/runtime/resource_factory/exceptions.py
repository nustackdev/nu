from __future__ import annotations

from loomicore.exceptions import ResourceError

__all__ = [
    "CreationError",
]


class FactoryError(ResourceError):
    """
    Base exception for resource factory-related errors.

    This exception is raised when the resource factory encounters issues
    that prevent it from creating or managing resources properly.
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
    """

    pass
