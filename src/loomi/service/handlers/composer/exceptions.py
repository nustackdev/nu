from __future__ import annotations

from typing import Any, Type

from loomi.service.exceptions import ServiceError

__all__ = [
    "DependencyError",
]


class DependencyError(ServiceError):
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
