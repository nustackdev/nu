from __future__ import annotations

from loomi.service.exceptions import ServiceError

__all__ = [
    "CircularDependencyError",
    "DependencyError",
    "DependencyNotFoundError",
]


class DependencyError(ServiceError):
    """Base exception for dependency-related errors."""

    pass


class DependencyNotFoundError(DependencyError):
    """Raised when dependency cannot be found or created."""

    pass


class CircularDependencyError(DependencyError):
    """Raised when circular dependency is detected."""

    pass
