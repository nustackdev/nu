from __future__ import annotations

from scriptable.app.exceptions import AppError

__all__ = [
    "ServiceDependencyError",
]


class ServiceDependencyError(AppError):
    """
    Raised for service-related errors.

    Examples:
    - Serivce dependency errors
    - Service lifecycle errors
    """

    pass
