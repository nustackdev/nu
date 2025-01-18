from ..exceptions import ServiceError


class DependencyError(ServiceError):
    """Base exception for dependency-related errors."""

    pass


class DependencyNotFoundError(DependencyError):
    """Raised when dependency cannot be found or created."""

    pass


class CircularDependencyError(DependencyError):
    """Raised when circular dependency is detected."""

    pass
