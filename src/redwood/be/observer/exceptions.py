"""Observer-specific exceptions."""

from __future__ import annotations

from redwood._rw_exception import RedwoodError


__all__ = [
    "ObserverConnectionError",
    "ObserverError",
    "ObserverSubscriptionError",
    "ObserverValidationError",
]


class ObserverError(RedwoodError):
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
