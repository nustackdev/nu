from __future__ import annotations

from loomi.app.exceptions import AppError

__all__ = [
    "InitializationError",
    "ShutdownError",
]


class InitializationError(AppError):
    """Raised when service initialization fails."""

    pass


class ShutdownError(AppError):
    """Raised when service shutdown fails."""

    pass
