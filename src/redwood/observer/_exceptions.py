from __future__ import annotations


__all__ = [
    "ObserverError",
    "ObserverConnectionError",
    "ObserverSubscriptionError",
    "ObserverValidationError",
]


class ObserverError(Exception):
    """Base exception for observer errors."""

    pass


class ObserverConnectionError(ObserverError):
    """Raised when observer connection fails."""

    pass


class ObserverSubscriptionError(ObserverError):
    """Raised when subscription operation fails."""

    pass


class ObserverValidationError(ObserverError):
    """Raised when subscription operation fails."""

    pass
