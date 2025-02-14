from __future__ import annotations

from loomi.service.exceptions import ServiceError

__all__ = [
    "InitializationError",
    "ShutdownError",
]


class InitializationError(ServiceError):
    """Raised when service initialization fails."""

    pass


class ShutdownError(ServiceError):
    """Raised when service shutdown fails."""

    pass
