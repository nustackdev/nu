from __future__ import annotations

from ..exceptions import ResourceError

__all__ = [
    "CircularDependencyError",
    "DependencyError",
    "DependencyNotFoundError",
]


class DependencyError(ResourceError):
    """Base exception for dependency-related errors."""

    pass


class DependencyNotFoundError(DependencyError):
    """Raised when dependency cannot be found or created."""

    pass


class CircularDependencyError(DependencyError):
    """Raised when circular dependency is detected."""

    pass
